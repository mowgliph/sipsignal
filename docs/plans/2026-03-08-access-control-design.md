# Diseño de Implementación para Control de Acceso del Bot sipsignal

## Visión General

Este documento detalla el diseño para implementar un sistema robusto de control de acceso en el bot de Telegram `sipsignal`. El objetivo es permitir o denegar el acceso a funcionalidades específicas del bot basándose en el estado de un usuario (no permitido, pendiente, aprobado, administrador), e incluir un mecanismo para que los usuarios soliciten acceso a los administradores.

## Componentes Clave

### 1. Modelo de Usuario (Database)

Se introducirá una nueva tabla `users` para gestionar el estado y los permisos de cada usuario que interactúa con el bot.

*   **Archivo:** `db/models/user.py`
*   **Modelo `User` (SQLAlchemy Declarative Base):**
    *   `id`: `Integer`, Primary Key. Identificador único de la base de datos.
    *   `chat_id`: `Integer`, `unique=True`, `nullable=False`. El ID de chat de Telegram del usuario, crucial para la identificación.
    *   `username`: `String`, `nullable=True`. Nombre de usuario de Telegram del usuario (opcional).
    *   `status`: `String`, `nullable=False`, `default='non_permitted'`. Define el nivel de acceso del usuario. Valores posibles:
        *   `'non_permitted'`: Usuario sin acceso. Necesita solicitar.
        *   `'pending'`: Usuario ha solicitado acceso y espera aprobación.
        *   `'approved'`: Acceso general al bot (excluye funciones de admin y logs).
        *   `'admin'`: Acceso total, incluyendo todas las funciones administrativas y de logs.
    *   `requested_at`: `DateTime`, `nullable=True`. Marca de tiempo de la última solicitud de acceso.

### 2. Lógica del Despachador Global (Middleware de Acceso)

Un componente crítico que actuará como un *middleware* para interceptar y gestionar todos los mensajes entrantes antes de que lleguen a los manejadores de comandos. Esto asegura que los usuarios no permitidos o pendientes reciban respuestas consistentes.

*   **Archivo:** `core/access_manager.py`
*   **Clase/Función `AccessManager` (o similar):**
    *   Se registrará como el *primer* `Handler` en el `telegram.ext.Dispatcher`.
    *   **Flujo de Procesamiento:**
        1.  **Extracción de `chat_id`**: Obtiene el `chat_id` del `update` de Telegram.
        2.  **Consulta/Creación de Usuario**:
            *   Intenta cargar el `User` desde la base de datos usando `chat_id`.
            *   Si el usuario no existe, se crea una nueva entrada en la base de datos con `status='non_permitted'`.
        3.  **Evaluación del Estado del Usuario (`user.status`):**
            *   **Si `user.status == 'non_permitted'`:**
                *   **Primera Solicitud o Solicitud Caducada**: Si `user.requested_at` es `None` o la última solicitud fue hace más de un período definido (ej., 24 horas para evitar spam):
                    *   Actualiza `user.status` a `'pending'` y `user.requested_at` a la hora actual.
                    *   Envía un mensaje al usuario: "Su solicitud de acceso ha sido enviada a los administradores. Por favor, espere la aprobación."
                    *   Envía una notificación a cada `chat_id` en `settings.ADMIN_CHAT_IDS` con los detalles del solicitante (`chat_id`, `username`) y los comandos sugeridos para aprobar/denegar.
                *   **Solicitud en Proceso**: Si `user.status` ya es `'pending'` (y la solicitud no ha caducado):
                    *   Envía un mensaje al usuario: "Su solicitud de acceso está siendo procesada. Le notificaremos una vez que sea revisada."
                *   **Detención del Flujo**: En ambos casos, el procesamiento del mensaje se detiene (`return ConversationHandler.END` o similar) para evitar que el mensaje llegue a otros manejadores de comandos.
            *   **Si `user.status == 'approved'` o `user.status == 'admin'`:**
                *   El `AccessManager` permite que el mensaje continúe su procesamiento normal por el `Dispatcher`, donde los decoradores de acceso específicos para los handlers aplicarán las restricciones finales.

### 3. Decoradores de Acceso

Se desarrollarán decoradores de Python para aplicar de forma declarativa las restricciones de acceso a las funciones de los manejadores de comandos.

*   **Archivo:** `utils/decorators.py`
*   **`@admin_only`:**
    *   **Propósito:** Restringe el acceso a un manejador de comandos solo a usuarios con `user.status == 'admin'`.
    *   **Implementación:** Envuelve la función del manejador. Antes de ejecutar la lógica del manejador, verifica el estado del usuario. Si el usuario no es `'admin'`, envía un mensaje de "Acceso denegado" al usuario y detiene la ejecución del manejador.
    *   **Aplicación:** Funciones de administración (ej., `/approve`, `/deny`, `/make_admin`, `/list_users`) y acceso a logs.
*   **`@permitted_only`:**
    *   **Propósito:** Restringe el acceso a un manejador de comandos a usuarios con `user.status == 'approved'` o `user.status == 'admin'`.
    *   **Implementación:** Similar a `@admin_only`, pero permite el paso a usuarios con `status='approved'` o `status='admin'`. Si el usuario no tiene ninguno de estos estados, envía un mensaje de "Acceso denegado" y detiene la ejecución.
    *   **Aplicación:** Funcionalidades centrales del bot que no son de administración (ej., comandos de trading, información de señales).

### 4. Comandos de Administración de Acceso

Se implementarán nuevos comandos para que los administradores gestionen las solicitudes y los estados de los usuarios.

*   **Archivo:** `handlers/admin_handlers.py`
*   **`/approve <chat_id>`:**
    *   **Protección:** `@admin_only`.
    *   **Funcionalidad:** Cambia el `status` del usuario con el `chat_id` especificado a `'approved'`.
    *   **Feedback:** Notifica al usuario que ha sido aprobado y al administrador que la operación fue exitosa.
*   **`/deny <chat_id>`:**
    *   **Protección:** `@admin_only`.
    *   **Funcionalidad:** Cambia el `status` del usuario con el `chat_id` especificado a `'non_permitted'`.
    *   **Feedback:** Notifica al usuario que su solicitud ha sido denegada y al administrador.
*   **`/make_admin <chat_id>`:**
    *   **Protección:** `@admin_only`.
    *   **Funcionalidad:** Cambia el `status` del usuario con el `chat_id` especificado a `'admin'`. (Considerar lógica para evitar la eliminación accidental de todos los administradores).
    *   **Feedback:** Notifica al usuario que ahora es administrador y al administrador que realizó la acción.
*   **`/list_users [status_filter]`:**
    *   **Protección:** `@admin_only`.
    *   **Funcionalidad:** Recupera y lista los usuarios registrados en la base de datos. Puede aceptar un argumento opcional `status_filter` (ej., `pending`, `approved`, `admin`) para filtrar la lista.
    *   **Feedback:** Envía la lista de usuarios al administrador.

### 5. Configuración y Arranque del Bot

Ajustes necesarios en la configuración y el punto de entrada principal del bot.

*   **`core/config.py`**:
    *   Añadir `ADMIN_CHAT_IDS: list[int]` para configurar los ID de chat de los administradores iniciales del bot. Esto es crucial para que el bot tenga al menos un administrador en su primera ejecución.
*   **`sipsignal.py` (Archivo Principal del Bot)**:
    *   **Inicialización de DB**: Asegurarse de que la base de datos y el modelo `User` se inicialicen correctamente al inicio.
    *   **Registro de `AccessManager`**: El `AccessManager` debe ser el primer `Handler` registrado en el `telegram.ext.Dispatcher` para garantizar que toda la lógica de control de acceso se ejecute antes que los manejadores de comandos específicos.
    *   **Registro de Handlers**: Todos los manejadores de comandos (existentes y nuevos) deben registrarse con el `Dispatcher`, aplicando los decoradores `@admin_only` o `@permitted_only` según sus requisitos de acceso.

## Exclusión de Funciones para Usuarios `Approved`

La restricción de que los usuarios `approved` no tendrán acceso al "log y a los servicios de administración" se gestionará mediante el uso exclusivo del decorador `@admin_only` en las funciones que caen en estas categorías. El decorador `@permitted_only` solo se aplicará a funcionalidades no administrativas, manteniendo así la segregación de privilegios.

## Resumen del Flujo de Interacción para Usuarios `non_permitted` / `pending`

1.  Un usuario (`non_permitted` o `pending`) envía cualquier mensaje/comando al bot.
2.  El `AccessManager` (como primer `Handler`) intercepta el mensaje.
3.  Consulta el estado del usuario en la base de datos.
4.  Si el estado es `'non_permitted'`:
    *   Marca al usuario como `'pending'` y registra la hora de la solicitud.
    *   Notifica al usuario que su solicitud ha sido enviada.
    *   Notifica a los administradores sobre la nueva solicitud.
5.  Si el estado es `'pending'`:
    *   Notifica al usuario que su solicitud está en proceso.
6.  En ambos casos (`'non_permitted'` o `'pending'`), el `AccessManager` impide que el mensaje continúe su procesamiento, protegiendo así el resto de los handlers.

---
