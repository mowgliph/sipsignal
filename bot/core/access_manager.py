"""
AccessManager - Middleware global para control de acceso.

Este módulo actúa como el primer punto de interceptación para todos los mensajes
entrantes del bot de Telegram. Gestiona el flujo de control de acceso:
- Crea usuarios automáticamente en la base de datos
- Evalúa el estado de acceso del usuario
- Maneja solicitudes de acceso para usuarios no permitidos o pendientes
- Notifica a los administradores sobre nuevas solicitudes
"""

from datetime import UTC, datetime, timedelta

from telegram import Bot, Update
from telegram.ext import Application

from bot.db.users import create_user, get_user, request_access
from bot.utils.inline_keyboards import build_access_keyboard
from bot.utils.logger import logger
from bot.utils.rate_limiter import AdminNotificationRateLimiter


class AccessManager:
    """
    Middleware global para control de acceso al bot.

    Esta clase debe ser registrada como el PRIMER handler en el dispatcher
    de Telegram para interceptar TODOS los mensajes entrantes antes de que
    lleguen a los handlers de comandos.

    El AccessManager:
    - Intercepta todos los updates entrantes
    - Crea usuarios automáticamente si no existen
    - Evalúa el estado de acceso (non_permitted, pending, approved, admin)
    - Maneja el flujo de solicitud de acceso
    - Notifica a los administradores sobre nuevas solicitudes
    - Detiene el procesamiento para usuarios no autorizados
    """

    # Mensajes en español (idioma por defecto del bot)
    MSG_REQUEST_SENT = (
        "✅ Su solicitud de acceso ha sido enviada a los administradores. "
        "Por favor, espere la aprobación."
    )

    MSG_REQUEST_PENDING = (
        "⏳ Su solicitud de acceso está siendo procesada. "
        "Le notificaremos una vez que sea revisada."
    )

    # Tiempo de expiración de solicitudes (24 horas)
    REQUEST_EXPIRY_HOURS = 24

    def __init__(self, admin_chat_ids: list[int]):
        """
        Inicializa el AccessManager.

        Args:
            admin_chat_ids: Lista de IDs de chat de administradores que recibirán
                           notificaciones sobre nuevas solicitudes de acceso.
        """
        self._admin_chat_ids = admin_chat_ids
        self._notification_limiter = AdminNotificationRateLimiter.get_instance()
        self._last_notification_user: dict[int, datetime] = {}
        self.NOTIFICATION_COOLDOWN_SECONDS = 60

    async def handle_update(self, update: Update, application: Application) -> bool:
        """
        Maneja un update entrante y decide si debe continuar procesándose.

        Este método es el punto de entrada principal del middleware. Debe ser
        llamado antes que cualquier otro handler en el dispatcher.

        Flujo:
        1. Extrae chat_id del update
        2. Omite updates que no sean mensajes (callback queries, etc.)
        3. Obtiene o crea el usuario en la base de datos
        4. Evalúa el estado del usuario:
           - 'non_permitted': Crea solicitud, notifica admins, envía mensaje al usuario, DETIENE
           - 'pending': Envía mensaje de "procesando", DETIENE
           - 'role_change_pending': Permite solo /help, /change_role, /my_role, DETIENE otros
           - 'viewer', 'trader', 'admin': Permite continuar (retorna True)
        5. Para solicitudes nuevas o expiradas (>24h), crea nueva solicitud

        Args:
            update: El update de Telegram a procesar
            application: La aplicación de Telegram

        Returns:
            True si el update debe continuar procesándose
            False si el procesamiento debe detenerse (usuario no autorizado)
        """
        # 1. Extraer chat_id del update
        chat_id = self._extract_chat_id(update)
        if chat_id is None:
            # No es un update con chat, permitir continuar
            return True

        # 2. Omitir updates que no sean mensajes
        if not self._is_message_update(update):
            return True

        # 3. Obtener o crear usuario en la base de datos
        username = self._extract_username(update)
        user = await self._get_or_create_user(chat_id, username)

        # 4. Evaluar estado del usuario
        status = user.get("status") if user else "non_permitted"
        requested_at = user.get("requested_at") if user else None

        # Obtener el bot de la aplicación
        bot = application.bot

        # Handle role_change_pending status (block most commands)
        if status == "role_change_pending":
            # Allow only /help, /change_role, /my_role
            message_text = update.message.text if update.message else ""
            allowed_commands = ("/help", "/change_role", "/my_role")

            if message_text in allowed_commands:
                # Allow these commands to pass through
                return True

            # Block other commands with informative message
            await self._send_message(
                bot,
                chat_id,
                "⏳ Tu solicitud de cambio de rol está siendo revisada. "
                "No puedes usar otros comandos hasta que sea aprobada.",
            )
            return False

        if status == "non_permitted":
            # Verificar si la solicitud está expirada (>24 horas)
            if self._is_request_expired(requested_at):
                # Crear nueva solicitud de acceso
                await request_access(chat_id)
                await self._notify_admins(bot, chat_id, username)
                await self._send_message(bot, chat_id, self.MSG_REQUEST_SENT)
            else:
                # Ya existe una solicitud válida, solo notificar al usuario
                await self._send_message(bot, chat_id, self.MSG_REQUEST_SENT)

            return False

        elif status == "pending":
            # Verificar si la solicitud está expirada
            if self._is_request_expired(requested_at):
                # Re-crear solicitud (resetear timer)
                await request_access(chat_id)
                await self._notify_admins(bot, chat_id, username)

            await self._send_message(bot, chat_id, self.MSG_REQUEST_PENDING)
            return False

        elif status in ("viewer", "trader", "admin"):
            # Usuario autorizado, permitir continuar
            return True

        # Por defecto, denegar acceso para estados desconocidos
        return False

    def _extract_chat_id(self, update: Update) -> int | None:
        """
        Extrae el chat_id de un update de Telegram.

        Args:
            update: El update de Telegram

        Returns:
            El chat_id si está disponible, None en caso contrario
        """
        if update.effective_chat:
            return update.effective_chat.id
        return None

    def _extract_username(self, update: Update) -> str | None:
        """
        Extrae el username de un update de Telegram.

        Args:
            update: El update de Telegram

        Returns:
            El username si está disponible, None en caso contrario
        """
        if update.effective_user:
            return update.effective_user.username
        return None

    def _is_message_update(self, update: Update) -> bool:
        """
        Verifica si el update es un mensaje de texto regular.

        Se omiten callback queries, ediciones de mensaje, y otros tipos
        de updates que no requieren control de acceso.

        Args:
            update: El update de Telegram

        Returns:
            True si es un mensaje regular, False en caso contrario
        """
        # Solo procesar mensajes regulares
        return update.message is not None

    async def _get_or_create_user(self, chat_id: int, username: str | None) -> dict:
        """
        Obtiene un usuario existente o crea uno nuevo en la base de datos.

        Args:
            chat_id: El ID de chat del usuario
            username: El username del usuario (opcional)

        Returns:
            Diccionario con los datos del usuario
        """
        user = await get_user(chat_id)

        if user is None:
            # Crear nuevo usuario con estado 'non_permitted' por defecto
            user = await create_user(chat_id)

        return user

    async def _notify_admins(self, bot: Bot, user_chat_id: int, username: str | None) -> None:
        """
        Notifica a todos los administradores sobre una nueva solicitud de acceso.

        Envía un mensaje a cada admin en admin_chat_ids con:
        - Chat ID del usuario solicitante
        - Username (si está disponible)
        - Timestamp de la solicitud
        - Botones inline para aprobar/denegar

        Args:
            bot: La instancia del bot de Telegram
            user_chat_id: El chat_id del usuario que solicitó acceso
            username: El username del usuario (opcional)
        """
        # Rate limiting - check if we should send notification
        limiter = AdminNotificationRateLimiter.get_instance()

        # Check cooldown for this specific user (don't spam about same user)
        now = datetime.now(UTC)
        last_notify = self._last_notification_user.get(user_chat_id)

        if last_notify and (now - last_notify).total_seconds() < self.NOTIFICATION_COOLDOWN_SECONDS:
            # Already notified recently about this user, skip
            return

        # Try to acquire rate limit slot
        if not await limiter.try_acquire():
            # Rate limited, skip notification but continue
            logger.warning(f"Admin notification rate limited, skipping for user {user_chat_id}")
            return

        # Update last notification time for this user
        self._last_notification_user[user_chat_id] = now

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Construir información del usuario
        user_info = f"Chat ID: `{user_chat_id}`"
        if username:
            user_info += f"\nUsername: @{username}"

        # Construir mensaje de notificación
        notification = (
            f"🔔 *Nueva Solicitud de Acceso*\n\n"
            f"{user_info}\n"
            f"🕒 Timestamp: {timestamp}\n\n"
            f"─────────────\n"
        )

        # Build inline keyboard with approve/deny buttons
        keyboard = build_access_keyboard(user_chat_id)

        # Enviar notificación a cada administrador
        for admin_id in self._admin_chat_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notification,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            except Exception as e:
                # Logear error pero continuar con los demás admins
                logger.error(f"Error al notificar admin {admin_id}: {e}")

    def _is_request_expired(self, requested_at: datetime | None) -> bool:
        """
        Verifica si una solicitud de acceso está expirada.

        Una solicitud se considera expirada si:
        - No existe timestamp (requested_at es None)
        - Han pasado más de 24 horas desde el timestamp

        Args:
            requested_at: El timestamp de cuando se creó la solicitud

        Returns:
            True si la solicitud está expirada o no existe, False en caso contrario
        """
        if requested_at is None:
            return True

        # Asegurar que requested_at tenga timezone info
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        expiry_threshold = now - timedelta(hours=self.REQUEST_EXPIRY_HOURS)

        return requested_at < expiry_threshold

    async def _send_message(self, bot: Bot, chat_id: int, text: str) -> None:
        """
        Envía un mensaje a un chat específico.

        Args:
            bot: La instancia del bot de Telegram
            chat_id: El ID del chat destino
            text: El texto del mensaje a enviar
        """
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
            )
        except Exception as e:
            logger.error(f"Error al enviar mensaje a {chat_id}: {e}")
