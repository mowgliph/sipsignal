"""Admin utility functions and decorators."""


# Función identidad para reemplazar i18n (textos ya están en español)
def _(message, *args, **kwargs):
    return message


def set_admin_util(func):
    """Permite a bbalert inyectar la función de envío masivo."""
    global _enviar_mensaje_telegram_async_ref
    _enviar_mensaje_telegram_async_ref = func


def set_logs_util(func):
    """Permite a bbalert inyectar la función para obtener los logs."""
    global _get_logs_data_ref
    _get_logs_data_ref = func


def _clean_markdown(text):
    """Clean text for Markdown by removing problematic characters.

    Replaces Markdown special chars with spaces to prevent parsing errors
    while keeping the text readable (no visible backslashes).
    """
    if text is None:
        return ""
    text = str(text)
    # Replace with spaces to avoid visible escape characters
    return (
        text.replace("_", " ")
        .replace("*", " ")
        .replace("`", " ")
        .replace("[", "(")
        .replace("]", ")")
    )


# Referencias para inyección de funciones (global state for dependency injection)
_enviar_mensaje_telegram_async_ref = None
_get_logs_data_ref = None
