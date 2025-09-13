# Realizado por:
# Samuel Jafet Juárez Baliño
# Leonardo Daniel Rosas Pérez
# José Jesús González Gallegos

# Se importa las librerías necesarias
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time

# Definición de la clase ClienteChat
class ClienteChat:
    # Inicializa el cliente de chat
    # - Define variables de conexión (socket, estado, usuario, host, puerto).
    # - Prepara variables de interfaz y almacenamiento de mensajes.
    # - Muestra la ventana inicial de conexión.
    def __init__(self):
        self.socket_cliente = None
        self.conectado = False
        self.nombre_usuario = ""
        self.host_servidor = ""
        self.puerto_servidor = 12345
        self.root = None
        self.usuarios_listbox = None
        self.chat_text = None
        self.mensaje_entry = None
        self.destinatario_var = None
        self.mensajes_privados = {} 
        self.mensajes_generales = []
        self.usuarios_con_mensajes_nuevos = set()
        self.combo_destinatario = None
        self.ventana_notificacion = None
        self.mostrar_ventana_conexion()

    # Muestra la ventana inicial para que el usuario configure:
    # - Nombre de usuario.
    # - Dirección IP del servidor.
    # - Puerto del servidor.
    # Permite intentar la conexión con un botón o presionando Enter.
    def mostrar_ventana_conexion(self):
        ventana_conexion = tk.Tk()
        ventana_conexion.title("🔗 Conectar al Chat")
        ventana_conexion.geometry("400x300")
        ventana_conexion.resizable(False, False)
        ventana_conexion.eval('tk::PlaceWindow . center')
        titulo = tk.Label(ventana_conexion, text="💬 Cliente de Chat", 
                         font=("Arial", 16, "bold"))
        titulo.pack(pady=20)
        frame_campos = tk.Frame(ventana_conexion)
        frame_campos.pack(pady=20, padx=40, fill="x")
        tk.Label(frame_campos, text="👤 Nombre de usuario:", font=("Arial", 10)).pack(anchor="w")
        self.entry_nombre = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_nombre.pack(fill="x", pady=(5, 15))
        tk.Label(frame_campos, text="🌐 IP del servidor:", font=("Arial", 10)).pack(anchor="w")
        self.entry_ip = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_ip.insert(0, "localhost")
        self.entry_ip.pack(fill="x", pady=(5, 15))
        tk.Label(frame_campos, text="🔌 Puerto del servidor:", font=("Arial", 10)).pack(anchor="w")
        self.entry_puerto = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_puerto.insert(0, "12345")
        self.entry_puerto.pack(fill="x", pady=(5, 15))
        btn_conectar = tk.Button(frame_campos, text="🚀 Conectar", 
                               font=("Arial", 12, "bold"),
                               bg="#4CAF50", fg="white",
                               command=lambda: self.intentar_conexion(ventana_conexion))
        btn_conectar.pack(pady=20, fill="x")
        ventana_conexion.bind('<Return>', lambda e: self.intentar_conexion(ventana_conexion))  
        ventana_conexion.mainloop()

    # Lee los datos ingresados por el usuario (nombre, IP, puerto),
    # valida que sean correctos y llama a `conectar_servidor`.
    # Si se conecta con éxito, abre la ventana principal del chat.
    def intentar_conexion(self, ventana_conexion):
        nombre = self.entry_nombre.get().strip()
        ip = self.entry_ip.get().strip()
        puerto = self.entry_puerto.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Por favor ingresa tu nombre de usuario")
            return
        if not ip:
            ip = "localhost"
        try:
            puerto = int(puerto) if puerto else 12345
        except ValueError:
            messagebox.showerror("Error", "Puerto inválido")
            return
        self.nombre_usuario = nombre
        self.host_servidor = ip
        self.puerto_servidor = puerto
        if self.conectar_servidor():
            ventana_conexion.destroy()
            self.mostrar_ventana_chat()
        else:
            messagebox.showerror("Error de Conexión", 
                               "No se pudo conectar al servidor.\n"
                               "Verifica que esté ejecutándose y los datos sean correctos.")
    
    # Crea el socket e intenta conectarse al servidor usando el protocolo:
    # - Envía comando `CONNECT|usuario`.
    # - Espera respuesta `SUCCESS`.
    # - Si es exitosa, arranca un hilo para recibir mensajes en segundo plano.
    def conectar_servidor(self):
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host_servidor, self.puerto_servidor))
            comando_conexion = f"CONNECT|{self.nombre_usuario}"
            self.socket_cliente.send(comando_conexion.encode('utf-8'))
            respuesta = self.socket_cliente.recv(1024).decode('utf-8')
            if respuesta.startswith("SUCCESS"):
                self.conectado = True
                hilo_recibir = threading.Thread(target=self.recibir_mensajes)
                hilo_recibir.daemon = True
                hilo_recibir.start()
                return True
            else:
                return False
        except Exception as e:
            print(f"Error conectando: {e}")
            return False
    
    # Construye la ventana principal del chat una vez conectado:
    # - Crea la interfaz gráfica.
    # - Solicita la lista de usuarios y el historial.
    # - Arranca actualizaciones periódicas de la lista de usuarios.
    def mostrar_ventana_chat(self):
        self.root = tk.Tk()
        self.root.title(f"💬 Chat - {self.nombre_usuario}")
        self.root.geometry("800x600")
        self.crear_interfaz_chat()
        self.solicitar_usuarios()
        self.solicitar_historial()
        self.actualizar_usuarios_periodicamente()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.mainloop()
    
    # Arma la interfaz gráfica:
    # - Panel izquierdo con lista de usuarios conectados.
    # - Panel derecho con selector de chat (general o privado), área de mensajes y caja de envío.
    def crear_interfaz_chat(self):
        frame_principal = tk.Frame(self.root)
        frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        frame_usuarios = tk.LabelFrame(frame_principal, text="👥 Usuarios Conectados", 
                                     font=("Arial", 12, "bold"))
        frame_usuarios.pack(side="left", fill="y", padx=(0, 10))
        self.usuarios_listbox = tk.Listbox(frame_usuarios, width=20, 
                                          font=("Arial", 10))
        self.usuarios_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.label_notificaciones = tk.Label(frame_usuarios, text="", 
                                           font=("Arial", 9), 
                                           fg="green")
        self.label_notificaciones.pack(padx=10, pady=(0, 10))
        frame_chat = tk.Frame(frame_principal)
        frame_chat.pack(side="right", fill="both", expand=True)
        frame_destinatario = tk.Frame(frame_chat)
        frame_destinatario.pack(fill="x", pady=(0, 10))
        tk.Label(frame_destinatario, text="💬 Chatear con:", 
                font=("Arial", 11)).pack(side="left")
        self.destinatario_var = tk.StringVar(value="🌐 Chat General")
        combo_destinatario = ttk.Combobox(frame_destinatario, 
                                         textvariable=self.destinatario_var,
                                         state="readonly",
                                         font=("Arial", 10))
        combo_destinatario.pack(side="left", padx=(10, 0), fill="x", expand=True)
        combo_destinatario.bind('<<ComboboxSelected>>', self.cambiar_chat)
        
        self.combo_destinatario = combo_destinatario  # Guardar referencia
        frame_mensajes = tk.LabelFrame(frame_chat, text="💭 Mensajes")
        frame_mensajes.pack(fill="both", expand=True, pady=(0, 10))
        frame_text = tk.Frame(frame_mensajes)
        frame_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_text = tk.Text(frame_text, state="disabled", 
                                font=("Arial", 10),
                                wrap="word")
        scrollbar = tk.Scrollbar(frame_text, orient="vertical", 
                               command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)   
        self.chat_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        frame_envio = tk.Frame(frame_chat)
        frame_envio.pack(fill="x")
        self.mensaje_entry = tk.Entry(frame_envio, font=("Arial", 11))
        self.mensaje_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_enviar = tk.Button(frame_envio, text="📤 Enviar", 
                             font=("Arial", 11, "bold"),
                             bg="#2196F3", fg="white",
                             command=self.enviar_mensaje)
        btn_enviar.pack(side="right")
        self.mensaje_entry.bind('<Return>', lambda e: self.enviar_mensaje())
    
    # Hilo que se mantiene escuchando mensajes del servidor.
    # Cuando recibe uno, lo pasa a `procesar_mensaje_recibido`.
    def recibir_mensajes(self):
        while self.conectado:
            try:
                mensaje = self.socket_cliente.recv(4096).decode('utf-8')
                if not mensaje:
                    break
                
                self.procesar_mensaje_recibido(mensaje)
                
            except Exception as e:
                if self.conectado:
                    print(f"Error recibiendo mensaje: {e}")
                break

    # Interpreta los mensajes recibidos según el protocolo.
    # Soporta comandos como:
    # - `USER_UPDATE` o `USER_LIST`: lista de usuarios conectados.
    # - `PRIVATE_MSG`: mensaje privado.
    # - `BROADCAST_MSG`: mensaje general.
    # - `HISTORY_MSG` y `HISTORY_END`: historial del chat.
    # - `USER_JOINED` y `USER_LEFT`: notificaciones de usuarios.
    # - `SUCCESS` y `ERROR`: confirmaciones o errores.
    def procesar_mensaje_recibido(self, mensaje):
        try:
            partes = mensaje.split('|', 2)
            comando = partes[0] 
            if comando == "USER_UPDATE" or comando == "USER_LIST":
                usuarios_texto = partes[1] if len(partes) > 1 else ""
                self.actualizar_lista_usuarios(usuarios_texto)
            elif comando == "PRIVATE_MSG":
                remitente = partes[1]
                contenido = partes[2] if len(partes) > 2 else ""
                self.recibir_mensaje_privado(remitente, contenido)
            elif comando == "BROADCAST_MSG":
                remitente = partes[1]
                contenido = partes[2] if len(partes) > 2 else ""
                self.recibir_mensaje_general(remitente, contenido)
            elif comando == "HISTORY_MSG":
                remitente = partes[1]
                contenido = partes[2] if len(partes) > 2 else ""
                self.recibir_mensaje_historial(remitente, contenido)
            elif comando == "HISTORY_END":
                self.finalizar_carga_historial()
            elif comando == "USER_JOINED":
                nombre_usuario = partes[1] if len(partes) > 1 else ""
                self.mostrar_notificacion_usuario_entro(nombre_usuario)
            elif comando == "USER_LEFT":
                nombre_usuario = partes[1] if len(partes) > 1 else ""
                self.mostrar_notificacion_usuario_salio(nombre_usuario)
            elif comando == "SUCCESS":
                pass 
            elif comando == "ERROR":
                error_msg = partes[1] if len(partes) > 1 else "Error desconocido"
                self.mostrar_error(error_msg)
        except Exception as e:
            print(f"Error procesando mensaje: {e}")

    # Actualiza la lista de usuarios conectados en el ListBox y en el Combobox de destinatarios
    def actualizar_lista_usuarios(self, usuarios_texto):
        if not self.usuarios_listbox:
            return
        usuarios = [u.strip() for u in usuarios_texto.split(',') if u.strip()]
        self.root.after(0, self._actualizar_listbox_usuarios, usuarios)
    
    # Método interno para refrescar la lista de usuarios y marcar cuáles tienen mensajes nuevos.
    def _actualizar_listbox_usuarios(self, usuarios):
        self.usuarios_listbox.delete(0, tk.END)
        otros_usuarios = [u for u in usuarios if u != self.nombre_usuario]
        for usuario in otros_usuarios:
            if usuario in self.usuarios_con_mensajes_nuevos:
                self.usuarios_listbox.insert(tk.END, f"🔴 {usuario}")
            else:
                self.usuarios_listbox.insert(tk.END, f"👤 {usuario}")
        valores = ["🌐 Chat General"]
        for usuario in otros_usuarios:
            if usuario in self.usuarios_con_mensajes_nuevos:
                valores.append(f"🔴 {usuario}")
            else:
                valores.append(f"👤 {usuario}")
        self.combo_destinatario['values'] = valores
        
    # Guarda un mensaje privado recibido y:
    # - Marca al remitente con notificación si no estamos viendo su chat.
    # - Si estamos en su chat, actualiza el área de mensajes.
    def recibir_mensaje_privado(self, remitente, contenido):
        if remitente not in self.mensajes_privados:
            self.mensajes_privados[remitente] = []
        timestamp = time.strftime("%H:%M:%S")
        mensaje_formateado = f"[{timestamp}] {remitente}: {contenido}"
        self.mensajes_privados[remitente].append(mensaje_formateado)
        destinatario_actual = self.destinatario_var.get()
        if destinatario_actual != f"👤 {remitente}" and destinatario_actual != f"🔴 {remitente}":
            self.usuarios_con_mensajes_nuevos.add(remitente)
            self.solicitar_usuarios()
            self.mostrar_notificacion_mensaje_privado(remitente)
        if destinatario_actual == f"👤 {remitente}" or destinatario_actual == f"🔴 {remitente}":
            self.root.after(0, self.actualizar_area_chat)
    
    # Agrega un mensaje al chat general y actualiza la vista si está abierto.
    def recibir_mensaje_general(self, remitente, contenido):
        timestamp = time.strftime("%H:%M:%S")
        mensaje_formateado = f"[{timestamp}] {remitente}: {contenido}"
        self.mensajes_generales.append(mensaje_formateado)
        if self.destinatario_var.get() == "🌐 Chat General":
            self.root.after(0, self.actualizar_area_chat)
            
    # Carga mensajes antiguos (historial) enviados por el servidor.
    def recibir_mensaje_historial(self, remitente, contenido):
        timestamp = time.strftime("%H:%M:%S")  # Usamos timestamp actual por simplicidad
        mensaje_formateado = f"[{timestamp}] {remitente}: {contenido}"
        self.mensajes_generales.append(mensaje_formateado)
    
    # Indica que ya se terminó de enviar el historial y refresca la vista.
    def finalizar_carga_historial(self):
        """NUEVO: Finaliza la carga del historial y actualiza la vista"""
        if self.destinatario_var.get() == "🌐 Chat General":
            self.root.after(0, self.actualizar_area_chat)

    # Muestra una notificación cuando un usuario se conecta al chat.
    def mostrar_notificacion_usuario_entro(self, nombre_usuario):
        mensaje = f"✅ {nombre_usuario} se unió al chat"
        self.root.after(0, lambda: self.actualizar_notificacion_temporal(mensaje, "green"))
        timestamp = time.strftime("%H:%M:%S")
        mensaje_sistema = f"[{timestamp}] SISTEMA: {mensaje}"
        self.mensajes_generales.append(mensaje_sistema)
        if self.destinatario_var.get() == "🌐 Chat General":
            self.root.after(0, self.actualizar_area_chat)

    # Muestra una notificación cuando un usuario se desconecta.
    def mostrar_notificacion_usuario_salio(self, nombre_usuario):
        mensaje = f"❌ {nombre_usuario} salió del chat"
        self.root.after(0, lambda: self.actualizar_notificacion_temporal(mensaje, "red"))
        timestamp = time.strftime("%H:%M:%S")
        mensaje_sistema = f"[{timestamp}] SISTEMA: {mensaje}"
        self.mensajes_generales.append(mensaje_sistema)
        if nombre_usuario in self.usuarios_con_mensajes_nuevos:
            self.usuarios_con_mensajes_nuevos.remove(nombre_usuario)
        if self.destinatario_var.get() == "🌐 Chat General":
            self.root.after(0, self.actualizar_area_chat)

    # Muestra una ventana emergente cuando llega un mensaje privado nuevo.
    def mostrar_notificacion_mensaje_privado(self, remitente):
        def crear_notificacion():
            if self.ventana_notificacion:
                try:
                    self.ventana_notificacion.destroy()
                except:
                    pass
            self.ventana_notificacion = tk.Toplevel(self.root)
            self.ventana_notificacion.title("💬 Nuevo Mensaje")
            self.ventana_notificacion.geometry("300x100")
            self.ventana_notificacion.resizable(False, False)
            x = self.root.winfo_x() + self.root.winfo_width() - 320
            y = self.root.winfo_y() + 50
            self.ventana_notificacion.geometry(f"300x100+{x}+{y}")
            self.ventana_notificacion.attributes('-topmost', True)
            frame = tk.Frame(self.ventana_notificacion, bg="#FFE4B5")
            frame.pack(fill="both", expand=True, padx=5, pady=5)
            tk.Label(frame, text="💬 Nuevo mensaje privado", 
                    font=("Arial", 11, "bold"), bg="#FFE4B5").pack(pady=5)
            tk.Label(frame, text=f"De: {remitente}", 
                    font=("Arial", 10), bg="#FFE4B5").pack()
            btn_ver = tk.Button(frame, text="Ver mensaje", 
                              command=lambda: self.ir_a_chat_privado(remitente),
                              bg="#4CAF50", fg="white")
            btn_ver.pack(side="left", padx=10, pady=10)
            btn_cerrar = tk.Button(frame, text="Cerrar", 
                                 command=self.ventana_notificacion.destroy,
                                 bg="#f44336", fg="white")
            btn_cerrar.pack(side="right", padx=10, pady=10)
            self.ventana_notificacion.after(5000, self.ventana_notificacion.destroy)
        self.root.after(0, crear_notificacion)
    
    # Cambia la vista al chat privado con el usuario seleccionado y marca sus mensajes como leídos.
    def ir_a_chat_privado(self, nombre_usuario):
        if self.ventana_notificacion:
            self.ventana_notificacion.destroy()
        self.destinatario_var.set(f"👤 {nombre_usuario}")
        if nombre_usuario in self.usuarios_con_mensajes_nuevos:
            self.usuarios_con_mensajes_nuevos.remove(nombre_usuario)
            self.solicitar_usuarios()
        self.actualizar_area_chat()

    # Muestra un mensaje breve en el área de notificaciones (ej. usuario entró o salió).
    def actualizar_notificacion_temporal(self, mensaje, color):
        if self.label_notificaciones:
            self.label_notificaciones.config(text=mensaje, fg=color)
            self.root.after(3000, lambda: self.label_notificaciones.config(text=""))
    
    # Se ejecuta al cambiar el destinatario en el ComboBox.
    # Marca como leídos los mensajes del usuario seleccionado.
    def cambiar_chat(self, event=None):
        destinatario = self.destinatario_var.get()
        if destinatario.startswith("🔴 "):
            nombre_usuario = destinatario.replace("🔴 ", "")
            if nombre_usuario in self.usuarios_con_mensajes_nuevos:
                self.usuarios_con_mensajes_nuevos.remove(nombre_usuario)
                self.solicitar_usuarios()  
        self.actualizar_area_chat()

    # Actualiza el área de texto del chat mostrando:
    # - Mensajes del chat general.
    # - Mensajes privados con el usuario seleccionado.
    def actualizar_area_chat(self):
        if not self.chat_text:
            return
        destinatario = self.destinatario_var.get()
        self.chat_text.config(state="normal")
        self.chat_text.delete(1.0, tk.END)
        if destinatario == "🌐 Chat General":
            for mensaje in self.mensajes_generales:
                if "SISTEMA:" in mensaje:
                    self.chat_text.insert(tk.END, mensaje + "\n")
                    line_start = self.chat_text.index("end-2l linestart")
                    line_end = self.chat_text.index("end-1l lineend")
                    self.chat_text.tag_add("sistema", line_start, line_end)
                    self.chat_text.tag_config("sistema", foreground="gray", font=("Arial", 9, "italic"))
                else:
                    self.chat_text.insert(tk.END, mensaje + "\n")
        else:
            if destinatario.startswith("🔴 "):
                nombre_usuario = destinatario.replace("🔴 ", "")
            else:
                nombre_usuario = destinatario.replace("👤 ", "")
            if nombre_usuario in self.mensajes_privados:
                for mensaje in self.mensajes_privados[nombre_usuario]:
                    self.chat_text.insert(tk.END, mensaje + "\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)
    
    # Envía un mensaje al servidor:
    # - Si es chat general → comando `BROADCAST|mensaje`.
    # - Si es privado → comando `MESSAGE|destinatario|mensaje`.
    # También lo agrega a la vista local.
    def enviar_mensaje(self):
        if not self.conectado:
            return
        mensaje = self.mensaje_entry.get().strip()
        if not mensaje:
            return
        destinatario = self.destinatario_var.get()
        if destinatario == "🌐 Chat General":
            comando = f"BROADCAST|{mensaje}"
        else:
            if destinatario.startswith("🔴 "):
                nombre_destinatario = destinatario.replace("🔴 ", "")
            else:
                nombre_destinatario = destinatario.replace("👤 ", "")
            comando = f"MESSAGE|{nombre_destinatario}|{mensaje}"
        try:
            self.socket_cliente.send(comando.encode('utf-8'))
            self.mensaje_entry.delete(0, tk.END)
            timestamp = time.strftime("%H:%M:%S")
            if destinatario == "🌐 Chat General":
                mensaje_formateado = f"[{timestamp}] Tú: {mensaje}"
                self.mensajes_generales.append(mensaje_formateado)
            else:
                if destinatario.startswith("🔴 "):
                    nombre_destinatario = destinatario.replace("🔴 ", "")
                else:
                    nombre_destinatario = destinatario.replace("👤 ", "")
                if nombre_destinatario not in self.mensajes_privados:
                    self.mensajes_privados[nombre_destinatario] = []
                mensaje_formateado = f"[{timestamp}] Tú: {mensaje}"
                self.mensajes_privados[nombre_destinatario].append(mensaje_formateado)
            self.actualizar_area_chat()
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
            messagebox.showerror("Error", "No se pudo enviar el mensaje")
    
    # Envía comando `GET_USERS` al servidor para obtener la lista de usuarios conectados.
    def solicitar_usuarios(self):
        if self.conectado:
            try:
                self.socket_cliente.send("GET_USERS|".encode('utf-8'))
            except:
                pass
    
    # Envía comando `GET_HISTORY` al servidor para obtener los últimos mensajes del chat general.
    def solicitar_historial(self):
        if self.conectado:
            try:
                self.socket_cliente.send("GET_HISTORY|".encode('utf-8'))
            except:
                pass
    
    # Cada 3 segundos pide al servidor la lista actualizada de usuarios.
    def actualizar_usuarios_periodicamente(self):
        if self.conectado:
            self.solicitar_usuarios()
            self.root.after(3000, self.actualizar_usuarios_periodicamente)
    
    # Muestra un cuadro de diálogo emergente con un mensaje de error.
    def mostrar_error(self, mensaje):
        self.root.after(0, lambda: messagebox.showerror("Error", mensaje))
    
    # Cierra correctamente la aplicación:
    # - Marca el cliente como desconectado.
    # - Cierra la ventana de notificación.
    # - Cierra el socket.
    # - Destruye la ventana principal.
    def cerrar_aplicacion(self):
        self.conectado = False
        if self.ventana_notificacion:
            try:
                self.ventana_notificacion.destroy()
            except:
                pass
        if self.socket_cliente:
            try:
                self.socket_cliente.close()
            except:
                pass
        if self.root:
            self.root.destroy()

# Si el programa se ejecuta directamente, inicia el cliente de chat
if __name__ == "__main__":
    cliente = ClienteChat()