# Mensajeria_Cliente-Servidor
**Actividad realizada por:**
_Samuel Jafet Juárez Baliño_
_Leonardo Daniel Rosas Pérez_
_José Jesús González Gallegos_

**Programa a realizar:**
Primer entregable de la materia de Tópicos para el despliegue de aplicaciones, donde estableceremos un protocolo (similar a los protocolos ya establecidos como HTTP, TCP/IP, UDP, etc.) para la comunicación de diversos clientes a través de un servidor en la misma red. Se implemetará el uso de sockets y una comunicación de mensajes en tiempo real para los diferentes usuarios que se conecten en tiempo real al servidor.

**Explicación del protocolo usado para la comunicación:**
Se decidió por implementar un protoclo que trabajara con cadenas de texto con formato específico, esto para facilitar la implementación del mismo y aplicar lo aprendido en otras materias que trabajan con patrones similares en los códigos de ciertas instrucciones.

**Estructura básica del protocolo (formato simple de texto):**
COMANDO|PARÁMETRO1|PARÁMETRO2|...

_Características de la estructura:_
- Separador: El carácter | (llamado pipe) separa los diferentes componentes de la instrucción a realizar.
- Encoding: UTF-8 para soportar caracteres especiales (como la ñ y acentos).
- Transporte: TCP ya que es muy usado para lo comunicación por la red.


**Comandos declarados para la comunicación cliente-servidor**
1. CONNECT - Para establecer la conexión
CONNECT|nombre_usuario

- Propósito: Registrar un nuevo cliente en el servidor
- Parámetros: nombre_usuario - Nombre único del cliente
- Ejemplo: CONNECT|Juan

- Flujo de funcionamiento de la instrucción:
Cliente se conecta al socket del servidor
Envía comando CONNECT con su nombre
Servidor valida que el nombre no esté en uso
Responde con SUCCESS o ERROR

2. MESSAGE - Mensaje privado
MESSAGE|destinatario|contenido_mensaje

- Propósito: Enviar mensaje privado a un usuario específico
- Parámetros:
destinatario - Usuario que recibirá el mensaje
contenido_mensaje - Texto del mensaje
- Ejemplo: MESSAGE|Maria|Hola, ¿cómo estás?

3. BROADCAST - Mensaje general
BROADCAST|contenido_mensaje

- Propósito: Enviar mensaje al chat general (todos los usuarios)
- Parámetros: contenido_mensaje - Texto del mensaje
- Ejemplo: BROADCAST|¡Hola a todos!

4. GET_USERS - Solicitar lista de usuarios
GET_USERS|

- Propósito: Obtener lista actual de usuarios conectados
- Parámetros: Ninguno (parámetro vacío)

5. GET_HISTORY - Solicitar historial
GET_HISTORY|

- Propósito: Obtener historial del chat general
- Parámetros: Ninguno

6. PING - Verificar conexión
PING

- Propósito: Verificar que la conexión siga activa
- Respuesta esperada: PONG


**Comandos declarados para las respuestas servidor-cliente**
_Respuestas de confirmación_

1. SUCCESS - Operación exitosa
SUCCESS|mensaje_descriptivo

- Ejemplo: SUCCESS|Conectado exitosamente
- Ejemplo: SUCCESS|Mensaje enviado al chat general

2. ERROR - Error en operación
ERROR|descripción_del_error

- Ejemplo: ERROR|Nombre ya existe
- Ejemplo: ERROR|Usuario no encontrado o desconectado

_Mensajes de datos_

3. USER_LIST / USER_UPDATE - Lista de usuarios
USER_LIST|usuario1,usuario2,usuario3
USER_UPDATE|usuario1,usuario2,usuario3

- USER_LIST: Respuesta a GET_USERS
- USER_UPDATE: Notificación automática cuando cambia la lista
- Formato: Nombres separados por comas

4. PRIVATE_MSG - Mensaje privado recibido
PRIVATE_MSG|remitente|contenido_mensaje

- Ejemplo: PRIVATE_MSG|Juan123|Hola, ¿cómo estás?

5. BROADCAST_MSG - Mensaje general recibido
BROADCAST_MSG|remitente|contenido_mensaje

- Ejemplo: BROADCAST_MSG|Maria|¡Buenos días a todos!

6. HISTORY_MSG - Mensaje del historial
HISTORY_MSG|remitente|contenido_mensaje

- Se envía secuencialmente para cada mensaje del historial

7. HISTORY_END - Fin del historial
HISTORY_END|

- Indica que se terminó de enviar el historial

_Notificaciones del sistema_

8. USER_JOINED - Usuario Se unió al chat
USER_JOINED|nombre_usuario

- Ejemplo: USER_JOINED|Pedro

9. USER_LEFT - Usuario salió del chat
USER_LEFT|nombre_usuario

- Ejemplo: USER_LEFT|Pedro


**Flujos de comunicación de los comandos**
_Flujo de conexión inicial_
1. Cliente → Servidor: CONNECT|Juan
2. Servidor → Cliente: SUCCESS|Conectado exitosamente
3. Servidor → Todos: USER_JOINED|Juan
4. Servidor → Todos: USER_UPDATE|Maria,Pedro,Juan
5. Cliente → Servidor: GET_HISTORY|
6. Servidor → Cliente: HISTORY_MSG|Pedro|Mensaje anterior...
7. Servidor → Cliente: HISTORY_END|

_Flujo de mensaje privado_
1. Juan → Servidor: MESSAGE|Maria|Hola Maria
2. Servidor → Maria: PRIVATE_MSG|Juan|Hola Maria
3. Servidor → Juan: SUCCESS|Mensaje enviado

_Flujo de mensaje general_
1. Juan → Servidor: BROADCAST|¡Hola todos!
2. Servidor → Maria: BROADCAST_MSG|Juan|¡Hola todos!
3. Servidor → Pedro: BROADCAST_MSG|Juan|¡Hola todos!
4. Servidor → Juan: SUCCESS|Mensaje enviado al chat general