# Design: Comando /status para SipSignal Bot

**Fecha:** 2025-03-05  
**Autor:** Kilo  
**Status:** Aprobado

---

## Resumen

Crear el comando `/status` como alias funcional del comando `/logs` existente, permitiendo a cualquier usuario consultar el estado básico del bot (versión, uptime, estado de servicios).

---

## Motivación

El bot actualmente no tiene un comando `/status`. Los usuarios necesitan poder verificar si el bot está funcionando correctamente sin necesidad de ser administradores. El comando `/logs` ya implementa esta funcionalidad para usuarios normales, mostrando información básica del sistema.

---

## Diseño

### Funcionalidad

El comando `/status` funcionará exactamente igual que `/logs` para usuarios no-admin:
- Versión del bot
- Estado del sistema
- Última actualización
- Mensaje de confirmación de operatividad

### Implementación

**Opción seleccionada:** Reutilizar la función `logs_command` existente y registrar un nuevo handler en `sipsignal.py`.

```python
# En sipsignal.py - agregar handler:
app.add_handler(CommandHandler("status", logs_command))
```

No requiere cambios en `admin.py` ya que `logs_command` ya maneja:
- Usuarios normales: muestra información básica
- Administradores: muestra logs completos

---

## Testing Strategy

1. **Setup:** Crear venv e instalar dependencias
2. **Unit Tests:** Verificar que el handler responde
3. **Integration Tests:** Verificar inicio del bot sin errores
4. **Command Tests:** Simular comando `/status`

---

## Criterios de Aceptación

- [ ] Bot inicia sin errores
- [ ] Comando `/status` responde con información del sistema
- [ ] Tests pasan exitosamente
- [ ] Código mergeado a main

---

## Notas

- No requiere cambios en lógica de negocio
- Reutiliza 100% código existente
- Mínimo riesgo de regresión
