# Realizado por:
# Samuel Jafet Juárez Baliño
# Leonardo Daniel Rosas Pérez
# José Jesús González Gallegos

# Se importa las librerías necesarias
import socket
import threading
import time
from datetime import datetime

# Definición de la clase ServidorChat
class ServidorChat:
    # Función que iicializa el servidor
    def __init__(self, host='localhost', puerto=12345):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        # Diccionario para almacenar clientes conectados
        self.clientes = {}  # Formato {nombre: {'socket': socket_obj, 'ip': direccion, 'conectado': True}}
        self.ejecutando = True
        
        # Historial de mensajes del chat general
        self.historial_general = []  # Lista de mensajes del chat general
        self.max_historial = 50  # Máximo de mensajes a mantener

    # Función que inicia el servidor    
    def iniciar_servidor(self):
        try:
            # Configuración del socket del servidor
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.puerto))
            self.socket_servidor.listen(10)
            
            # Mensajes de estado
            print(f"Servidor de chat iniciado en {self.host}:{self.puerto}")
            print("Protocolo personalizado activado")
            print("Historial de chat general habilitado")
            print("Presiona Ctrl+C para detener")
            
            # Bucle principal para aceptar conexiones
            while self.ejecutando:
                try:
                    # Aceptar nueva conexión
                    cliente_socket, direccion = self.socket_servidor.accept()
                    print(f"Nueva conexión desde {direccion}")
                    
                    # Crear hilo para manejar este cliente
                    hilo_cliente = threading.Thread(
                        target=self.manejar_cliente,
                        args=(cliente_socket, direccion)
                    )
                    hilo_cliente.daemon = True
                    hilo_cliente.start()
                    
                except Exception as e: # Manejo de errores al aceptar conexiones
                    if self.ejecutando:
                        print(f"Error aceptando conexión: {e}")
                        
        except KeyboardInterrupt: # Manejo de Ctrl+C para detener el servidor
            print("\nDeteniendo servidor...")
        except Exception as e: # Manejo de otros errores
            print(f"Error iniciando servidor: {e}")
        finally: # Asegurar que el servidor se detenga correctamente
            self.detener_servidor()
    
    # Función que maneja la comunicación con un cliente
    def manejar_cliente(self, cliente_socket, direccion):
        nombre_cliente = None
        
        try:
            while self.ejecutando:
                try:
                    # Recibir mensaje del cliente
                    data = cliente_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    # Procesar mensaje según el protocolo
                    respuesta = self.procesar_mensaje_protocolo(data, cliente_socket, direccion, nombre_cliente)
                    
                    # Si el cliente se registró, actualizar su nombre
                    if respuesta and 'nombre_registrado' in respuesta:
                        nombre_cliente = respuesta['nombre_registrado']
                    
                except socket.error:
                    break
                    
        except Exception as e: # Manejo de errores generales
            print(f"Error manejando cliente {direccion}: {e}")
        finally:
            # Limpiar cliente al desconectarse
            if nombre_cliente and nombre_cliente in self.clientes:
                del self.clientes[nombre_cliente]
                print(f"{nombre_cliente} se desconectó")
                
                # Notificar salida del usuario
                self.notificar_usuario_salio(nombre_cliente)
                # Notificar a todos sobre la desconexión
                self.notificar_cambio_usuarios()
            
            cliente_socket.close() # Cerrar socket del cliente
    
    # Función que procesa los mensajes según el protocolo personalizado
    def procesar_mensaje_protocolo(self, mensaje, cliente_socket, direccion, nombre_actual):
        """Procesa mensajes según nuestro protocolo personalizado"""
        try:
            # El protocolo usa un formato: COMANDO|PARAMETROS
            partes = mensaje.split('|', 1) # Dividir en comando y parámetros
            comando = partes[0] # Primer parte es el comando
            parametros = partes[1] if len(partes) > 1 else ""  # Resto son parámetros
            
            if comando == "CONNECT": # Manejar conexión inicial
                return self.manejar_conexion(parametros, cliente_socket, direccion)
            
            elif comando == "MESSAGE": # Manejar mensaje privado
                return self.manejar_mensaje_privado(parametros, nombre_actual)
            
            elif comando == "BROADCAST": # Manejar mensaje al chat general
                return self.manejar_mensaje_general(parametros, nombre_actual)
            
            elif comando == "GET_USERS": # Enviar lista de usuarios conectados
                return self.enviar_lista_usuarios(cliente_socket)
            
            elif comando == "GET_HISTORY": # Enviar historial del chat general
                return self.enviar_historial_general(cliente_socket)
            
            elif comando == "PING": # Responder a ping
                cliente_socket.send("PONG".encode('utf-8'))
                return None
            
            else: # Comando no reconocido
                cliente_socket.send("ERROR|Comando no reconocido".encode('utf-8'))
                return None
                
        except Exception as e: # Manejo de errores al procesar mensajes
            print(f"Error procesando mensaje: {e}")
            cliente_socket.send("ERROR|Error procesando mensaje".encode('utf-8'))
            return None
    
    # Función que maneja el registro de un nuevo cliente
    def manejar_conexion(self, nombre, cliente_socket, direccion):
        if not nombre.strip(): # Validar nombre no vacío
            cliente_socket.send("ERROR|Nombre vacío".encode('utf-8'))
            return None
        
        if nombre in self.clientes: # Validar nombre único
            cliente_socket.send("ERROR|Nombre ya existe".encode('utf-8'))
            return None
        
        # Registrar cliente
        self.clientes[nombre] = {
            'socket': cliente_socket, # Guardar el socket del cliente
            'ip': direccion[0], # Guardar la IP del cliente
            'puerto': direccion[1], # Guardar el puerto del cliente
            'conectado': True # Estado de conexión
        }
        
        # Confirmar registro
        print(f"{nombre} registrado desde {direccion}")
        cliente_socket.send("SUCCESS|Conectado exitosamente".encode('utf-8'))
        
        # Notificar entrada del usuario a todos los demás usuarios
        self.notificar_usuario_entro(nombre)
        
        # Notificar a todos los clientes sobre el nuevo usuario
        self.notificar_cambio_usuarios()
        
        return {'nombre_registrado': nombre} # Retornar el nombre registrado
    
    # Función que maneja mensajes privados entre usuarios
    def manejar_mensaje_privado(self, parametros, remitente):
        if not remitente or remitente not in self.clientes: # Validar remitente
            return None
        
        try: # Procesar mensaje privado
            # Formato: DESTINATARIO|MENSAJE
            partes = parametros.split('|', 1) # Dividir en destinatario y mensaje
            destinatario = partes[0] # Primer parte es el destinatario
            mensaje = partes[1] if len(partes) > 1 else "" # Resto es el mensaje
            
            # Validar destinatario
            if destinatario in self.clientes and self.clientes[destinatario]['conectado']:
                # Enviar mensaje al destinatario
                mensaje_formateado = f"PRIVATE_MSG|{remitente}|{mensaje}"
                self.clientes[destinatario]['socket'].send(mensaje_formateado.encode('utf-8'))
                
                # Confirmar envío al remitente
                self.clientes[remitente]['socket'].send("SUCCESS|Mensaje enviado".encode('utf-8'))
                print(f"{remitente} → {destinatario}: {mensaje}")
                
            else:
                # Destinatario no encontrado o desconectado
                self.clientes[remitente]['socket'].send("ERROR|Usuario no encontrado o desconectado".encode('utf-8'))
                
        except Exception as e: # Manejo de errores al enviar mensaje privado
            print(f"Error enviando mensaje privado: {e}")
    
    # Función que maneja mensajes al chat general
    def manejar_mensaje_general(self, mensaje, remitente):
        if not remitente or remitente not in self.clientes: # Validar remitente
            return None
        
        print(f"{remitente} (general): {mensaje}")
        
        # Agregar mensaje al historial
        timestamp = datetime.now().strftime("%H:%M:%S")
        mensaje_con_timestamp = {
            'timestamp': timestamp, # Hora del mensaje
            'remitente': remitente, # Quién envió el mensaje
            'mensaje': mensaje # Contenido del mensaje
        }
        
        self.historial_general.append(mensaje_con_timestamp)
        
        # Mantener solo los últimos 50 mensajes
        if len(self.historial_general) > self.max_historial:
            self.historial_general.pop(0)
        
        # Enviar a todos los clientes conectados
        mensaje_formateado = f"BROADCAST_MSG|{remitente}|{mensaje}"
        clientes_desconectados = [] # Lista para limpiar clientes desconectados
        
        # Reenviar mensaje a todos excepto al remitente
        for nombre, info in self.clientes.items():
            if info['conectado'] and nombre != remitente:  # No reenviar al remitente
                try: # Intentar enviar el mensaje
                    info['socket'].send(mensaje_formateado.encode('utf-8'))
                except: # Si falla, marcar como desconectado
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
        
        # Confirmar envío
        try:
            self.clientes[remitente]['socket'].send("SUCCESS|Mensaje enviado al chat general".encode('utf-8'))
        except: # Si falla el envío al remitente
            pass
    
    # Función que envía la lista de usuarios conectados al cliente
    def enviar_lista_usuarios(self, cliente_socket):
        usuarios = list(self.clientes.keys()) 
        lista_usuarios = ','.join(usuarios) 
        mensaje = f"USER_LIST|{lista_usuarios}" 
        cliente_socket.send(mensaje.encode('utf-8')) 
    
    # Función que envía el historial del chat general al cliente
    def enviar_historial_general(self, cliente_socket):
        try: # Enviar cada mensaje del historial
            for msg in self.historial_general:
                mensaje_formateado = f"HISTORY_MSG|{msg['remitente']}|{msg['mensaje']}" # Formato del mensaje
                cliente_socket.send(mensaje_formateado.encode('utf-8'))
                time.sleep(0.01)  # Pequeña pausa para evitar saturar
            
            # Señal de fin de historial
            cliente_socket.send("HISTORY_END|".encode('utf-8'))
        except Exception as e: # Manejo de errores al enviar historial
            print(f"Error enviando historial: {e}")
    
    # Función que notifica a todos los clientes sobre cambios en la lista de usuarios
    def notificar_cambio_usuarios(self):
        usuarios = list(self.clientes.keys()) # Obtener lista de usuarios
        lista_usuarios = ','.join(usuarios)
        mensaje = f"USER_UPDATE|{lista_usuarios}" # Formato del mensaje
        
        clientes_desconectados = [] # Lista para limpiar clientes desconectados
        for nombre, info in self.clientes.items(): # Enviar a todos los clientes
            try:
                info['socket'].send(mensaje.encode('utf-8'))
            except:
                clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
    
    # Función que notifica a todos los clientes que un usuario se ha unido al chat
    def notificar_usuario_entro(self, nombre_usuario):
        mensaje = f"USER_JOINED|{nombre_usuario}" # Formato del mensaje
        clientes_desconectados = [] # Lista para limpiar clientes desconectados
        
        for nombre, info in self.clientes.items():
            if nombre != nombre_usuario:  # No notificar al usuario que acaba de entrar
                try:
                    info['socket'].send(mensaje.encode('utf-8'))
                except:
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
    
    # Función que notifica a todos los clientes que un usuario ha salido del chat
    def notificar_usuario_salio(self, nombre_usuario):
        mensaje = f"USER_LEFT|{nombre_usuario}" # Formato del mensaje
        clientes_desconectados = [] # Lista para limpiar clientes desconectados
        
        for nombre, info in self.clientes.items():
            if nombre != nombre_usuario:  # No notificar al usuario que acaba de salir
                try:
                    info['socket'].send(mensaje.encode('utf-8'))
                except:
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            if nombre in self.clientes:
                del self.clientes[nombre]
    
    # Función que detiene el servidor y cierra todas las conexiones
    def detener_servidor(self):
        print("Cerrando servidor...")
        self.ejecutando = False
        
        # Cerrar todas las conexiones
        for info in self.clientes.values():
            try: 
                info['socket'].close()
            except:
                pass
        
        # Cerrar socket servidor
        if self.socket_servidor:
            try:
                self.socket_servidor.close()
            except:
                pass
        
        print("Servidor cerrado")

# Si el programa se ejecuta directamente, inicia el servidor
if __name__ == "__main__":
    servidor = ServidorChat()
    
    try: 
        servidor.iniciar_servidor() # Iniciar el servidor
    except KeyboardInterrupt:
        servidor.detener_servidor() # Manejo de Ctrl+C para detener el servidor