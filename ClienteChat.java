package Topicos_despliegue.Servidor_cliente;

//Importaciones necesarias
import javax.swing.*;
import javax.swing.Timer;
import java.awt.*;
import java.io.*;
import java.net.Socket;
import java.util.*;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Cliente de chat con interfaz gráfica que implementa un protocolo
 * personalizado
 * para comunicación con el servidor. Soporta mensajería privada, chat general,
 * historial de mensajes y notificaciones en tiempo real.
 * 
 * Protocolo utilizado:
 * - CONNECT|nombre: Registro de usuario
 * - MESSAGE|destinatario|mensaje: Mensaje privado
 * - BROADCAST|mensaje: Mensaje al chat general
 * - GET_USERS: Solicitar lista de usuarios conectados
 * - GET_HISTORY: Solicitar historial del chat general
 * 
 * @author Samuel Juárez, Jesús González y Leonardo Rosas 
 * @version 1.0
 */

public class ClienteChat {
    //Variables de conexión
    private Socket socketCliente;
    private PrintWriter salida;
    private BufferedReader entrada;
    private boolean conectado = false;

    //Variables de usuario y servidor
    private String nombreUsuario;
    private String hostServidor;
    private int puertoServidor;

    //Componentes de la interfaz gráfica
    private JFrame ventanaChat;
    private JTextArea areaChat;
    private JTextField campoMensaje;
    private JComboBox<String> comboDestinatario;
    private DefaultListModel<String> modeloUsuarios;
    private JList<String> listaUsuarios;
    private JLabel labelNotificaciones;

    //Variables de estado de los mensajes
    //En esta variable se almacenan los mensajes privados organizados por usuario remitente
    private final Map<String, List<String>> mensajesPrivados = new ConcurrentHashMap<>();
    //Lista de mensajes del chat general
    private final List<String> mensajesGenerales = Collections.synchronizedList(new ArrayList<>());
    //Usuario con mensajes no leídos
    private final Set<String> usuariosConMensajesNuevos = Collections.synchronizedSet(new HashSet<>());

    //Ventana de notificación emergente
    private JDialog ventanaNotificacion;

    //Método principal para iniciar la aplicación
    public static void main(String[] args) {
        SwingUtilities.invokeLater(ClienteChat::new);
    }

    
    //Constructor que inicia la aplicación mostrando la ventana de conexión
     
    public ClienteChat() {
        mostrarVentanaConexion();
    }

    
    //Muestra el diálogo inicial para configurar y establecer conexión con el servidor
    private void mostrarVentanaConexion() {
        //Configuración de la ventana principal
        JFrame ventana = new JFrame("Conectar al Chat");
        ventana.setSize(400, 300);
        ventana.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        ventana.setLayout(new BorderLayout());
        ventana.setLocationRelativeTo(null);

        //Título principal
        JLabel titulo = new JLabel("Cliente de Chat", SwingConstants.CENTER);
        titulo.setFont(new Font("Arial", Font.BOLD, 18));
        ventana.add(titulo, BorderLayout.NORTH);

        //Panel de campos de entrada
        JPanel panel = new JPanel(new GridLayout(6, 1, 5, 5));
        JTextField campoNombre = new JTextField();
        JTextField campoIP = new JTextField("localhost");
        JTextField campoPuerto = new JTextField("12345");

        // Etiquetas con emojis para mejor entendimiento de los usuarios
        panel.add(new JLabel("👤 Nombre de usuario:"));
        panel.add(campoNombre);
        panel.add(new JLabel("🌐 IP del servidor:"));
        panel.add(campoIP);
        panel.add(new JLabel("🔌 Puerto del servidor:"));
        panel.add(campoPuerto);

        //Añadir panel al centro de la ventana
        ventana.add(panel, BorderLayout.CENTER);

        //Botón de conexión 
        JButton btnConectar = new JButton("Conectar");
        btnConectar.setBackground(new Color(0, 150, 0));
        btnConectar.setForeground(Color.WHITE);
        ventana.add(btnConectar, BorderLayout.SOUTH);

        //Acción al presionar el botón de conectar
        btnConectar.addActionListener(e -> {
            //Obtener datos de los campos
            nombreUsuario = campoNombre.getText().trim();
            hostServidor = campoIP.getText().trim();
            try {
                //Validar que el puerto sea un número válido
                puertoServidor = Integer.parseInt(campoPuerto.getText().trim());
            } catch (NumberFormatException ex) {
                puertoServidor = 12345; //Puerto por defecto si la entrada es inválida
            }

            //Validar que el nombre de usuario no esté vacío
            if (nombreUsuario.isEmpty()) {
                JOptionPane.showMessageDialog(ventana, "Debes ingresar un nombre de usuario", "Error",
                        JOptionPane.ERROR_MESSAGE);
                return;
            }

            //Intentar conectar al servidor
            if (conectarServidor()) {
                ventana.dispose();
                mostrarVentanaChat();
            } else {
                //Mostrar error si la conexión falla
                JOptionPane.showMessageDialog(ventana, "No se pudo conectar al servidor", "Error",
                        JOptionPane.ERROR_MESSAGE);
            }
        });

        //Permitir presionar Enter para conectar
        ventana.getRootPane().setDefaultButton(btnConectar);
        ventana.setVisible(true);
    }

    //Establece la conexión TCP con el servidor y realiza el handshake inicial
    //@return true si la conexión y registro fueron exitosos, false en caso contrario
    private boolean conectarServidor() {
        try {
            //Crear socket y flujos de entrada/salida
            socketCliente = new Socket(hostServidor, puertoServidor);
            salida = new PrintWriter(socketCliente.getOutputStream(), true);
            entrada = new BufferedReader(new InputStreamReader(socketCliente.getInputStream()));

            //Enviar comando de registro según protocolo: CONNECT|nombre
            salida.println("CONNECT|" + nombreUsuario);
            String respuesta = entrada.readLine();

            //Esperar respuesta del servidor
            if (respuesta != null && respuesta.startsWith("SUCCESS")) {
                //Conexión exitosa
                conectado = true;
                // Iniciar hilo para recepción continua de mensajes
                new Thread(this::recibirMensajes).start();
                return true;
            }
        } catch (Exception e) {
            //En caso de error de conexión, imprimir el error en consola
            e.printStackTrace();
        }
        return false;
    }


     //Construye y muestra la interfaz principal del chat con dos paneles:
     //- Panel izquierdo: Lista de usuarios conectados
     //- Panel derecho: Área de chat y controles de envío
    private void mostrarVentanaChat() {
        //Configuración de la ventana principal del chat
        ventanaChat = new JFrame("💬 Chat - " + nombreUsuario);
        ventanaChat.setSize(800, 600);
        ventanaChat.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        ventanaChat.setLayout(new BorderLayout());

        //Panel de usuarios conectados (izquierda)
        JPanel panelUsuarios = new JPanel(new BorderLayout());
        panelUsuarios.setBorder(BorderFactory.createTitledBorder("👥 Usuarios Conectados"));
        modeloUsuarios = new DefaultListModel<>();
        listaUsuarios = new JList<>(modeloUsuarios);
        panelUsuarios.add(new JScrollPane(listaUsuarios), BorderLayout.CENTER);

        //Label para notificaciones de estado (conexiones/desconexiones)
        labelNotificaciones = new JLabel(" ");
        panelUsuarios.add(labelNotificaciones, BorderLayout.SOUTH);

        //Panel principal de chat (derecha)
        JPanel panelChat = new JPanel(new BorderLayout());

        //Selector de destinatario (Chat General o usuario específico)
        JPanel panelDestinatario = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panelDestinatario.add(new JLabel("💬 Chatear con:"));
        comboDestinatario = new JComboBox<>(new String[] { "🌐 Chat General" });
        panelDestinatario.add(comboDestinatario);
        panelChat.add(panelDestinatario, BorderLayout.NORTH);

        //Área principal de visualización de mensajes
        areaChat = new JTextArea();
        areaChat.setEditable(false);
        panelChat.add(new JScrollPane(areaChat), BorderLayout.CENTER);

        //Panel inferior para escribir y enviar mensajes
        JPanel panelEnvio = new JPanel(new BorderLayout());
        campoMensaje = new JTextField();
        JButton btnEnviar = new JButton("📤 Enviar");
        btnEnviar.setBackground(new Color(0, 100, 200));
        btnEnviar.setForeground(Color.WHITE);

        btnEnviar.addActionListener(e -> enviarMensaje());
        campoMensaje.addActionListener(e -> enviarMensaje()); //Presionar Enter para enviar

        //Añadir componentes al panel de envío
        panelEnvio.add(campoMensaje, BorderLayout.CENTER);
        panelEnvio.add(btnEnviar, BorderLayout.EAST);
        panelChat.add(panelEnvio, BorderLayout.SOUTH);

        //Añadir ambos paneles a la ventana principal
        ventanaChat.add(panelUsuarios, BorderLayout.WEST);
        ventanaChat.add(panelChat, BorderLayout.CENTER);

        ventanaChat.setVisible(true);

        //Solicitar lista inicial de usuarios y cargar historial de mensajes
        solicitarUsuarios();
        solicitarHistorial();
        // Timer para actualización periódica de la lista de usuarios
        new Timer(3000, e -> solicitarUsuarios()).start();
    }


    //Hilo de recepción continua de mensajes del servidor.
    //Se ejecuta en un hilo separado para no bloquear la interfaz.
    private void recibirMensajes() {
        try {
            //Leer mensajes del servidor hasta que la conexión se cierre
            String mensaje;
            while ((mensaje = entrada.readLine()) != null && conectado) {
                procesarMensaje(mensaje);
            }
        } catch (IOException e) {
            //Si la conexión se pierde inesperadamente, mostrar notificación
            if (conectado)
                e.printStackTrace();
        }
    }

    /**
    * Procesa los mensajes recibidos del servidor según el protocolo establecido
    * 
    * Tipos de mensaje soportados:
    * - USER_LIST/USER_UPDATE: Actualización de usuarios conectados
    * - PRIVATE_MSG: Mensaje privado recibido
    * - BROADCAST_MSG: Mensaje del chat general
    * - HISTORY_MSG: Mensaje del historial
    * - USER_JOINED/USER_LEFT: Notificaciones de conexión/desconexión
    * - ERROR: Mensajes de error del servidor
    * 
    * @param mensaje Mensaje crudo recibido del servidor en formato
    *                COMANDO|PARAMETROS
    */
    private void procesarMensaje(String mensaje) {
        try {
            String[] partes = mensaje.split("\\|", 3);
            String comando = partes[0];

            switch (comando) {
                // Actualizar lista de usuarios conectados
                case "USER_LIST":
                case "USER_UPDATE":
                    SwingUtilities.invokeLater(() -> actualizarListaUsuarios(partes.length > 1 ? partes[1] : ""));
                    break;
                case "PRIVATE_MSG": //Mensaje privado recibido
                    String remitente = partes[1];
                    String contenidoPrivado = partes.length > 2 ? partes[2] : "";
                    recibirMensajePrivado(remitente, contenidoPrivado);
                    break;
                case "BROADCAST_MSG": //Mensaje del chat general
                    String remitenteG = partes[1];
                    String contenidoG = partes.length > 2 ? partes[2] : "";
                    recibirMensajeGeneral(remitenteG, contenidoG);
                    break;
                case "HISTORY_MSG": 
                    // Los mensajes del historial se tratan como mensajes generales
                    recibirMensajeGeneral(partes[1], partes.length > 2 ? partes[2] : "");
                    break;
                case "USER_JOINED": //Notificación de usuario conectado
                    mostrarNotificacionTemporal("✅ " + partes[1] + " se unió al chat", Color.GREEN);
                    break;
                case "USER_LEFT": //Notificación de usuario desconectado
                    mostrarNotificacionTemporal("❌ " + partes[1] + " salió del chat", Color.RED);
                    break;
                case "ERROR": //Mensaje de error del servidor
                    JOptionPane.showMessageDialog(ventanaChat, partes[1], "Error", JOptionPane.ERROR_MESSAGE);
                    break;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
    * Actualiza la lista visual de usuarios conectados y el combo de destinatarios.
    * Aplica indicadores visuales para usuarios con mensajes no leídos.
    * 
    * @param usuariosTexto Lista de usuarios separados por comas recibida del
    *                      servidor
    */
    private void actualizarListaUsuarios(String usuariosTexto) {
        // Limpiar lista actual
        modeloUsuarios.clear();
        comboDestinatario.removeAllItems();
        comboDestinatario.addItem("🌐 Chat General");

        // Añadir usuarios a la lista y al combo, aplicando indicadores visuales
        for (String usuario : usuariosTexto.split(",")) {
            usuario = usuario.trim();
            //Evitar añadir el propio usuario
            if (!usuario.isEmpty() && !usuario.equals(nombreUsuario)) {
                // Aplicar indicador visual para usuarios con mensajes no leídos
                if (usuariosConMensajesNuevos.contains(usuario)) {
                    modeloUsuarios.addElement("🔴 " + usuario);
                    comboDestinatario.addItem("🔴 " + usuario);
                } else { // Usuario sin mensajes nuevos
                    modeloUsuarios.addElement("👤 " + usuario);
                    comboDestinatario.addItem("👤 " + usuario);
                }
            }
        }
    }

    /**
    * Procesa la recepción de un mensaje privado de otro usuario
    * 
    * @param remitente Usuario que envió el mensaje
    * @param contenido Texto del mensaje recibido
    */
    private void recibirMensajePrivado(String remitente, String contenido) {
        // Almacenar mensaje en la conversación correspondiente
        mensajesPrivados.computeIfAbsent(remitente, k -> new ArrayList<>())
                .add(formatearMensaje(remitente, contenido));

        // Si no estamos viendo la conversación con este usuario, marcar como no leído
        if (!comboDestinatario.getSelectedItem().toString().contains(remitente)) {
            usuariosConMensajesNuevos.add(remitente);
            mostrarNotificacionPrivada(remitente);
            solicitarUsuarios(); // Refrescar lista para mostrar indicador visual
        }

        // Si estamos viendo esta conversación, actualizar el área de chat
        if (comboDestinatario.getSelectedItem().toString().contains(remitente)) {
            actualizarAreaChat();
        }
    }

    /**
    * Procesa la recepción de un mensaje del chat general
    * 
    * @param remitente Usuario que envió el mensaje
    * @param contenido Texto del mensaje
    */
    private void recibirMensajeGeneral(String remitente, String contenido) {
        mensajesGenerales.add(formatearMensaje(remitente, contenido));
        // Actualizar vista solo si estamos viendo el chat general
        if ("🌐 Chat General".equals(comboDestinatario.getSelectedItem().toString())) {
            actualizarAreaChat();
        }
    }

    /**
    * Formatea un mensaje con timestamp para su visualización
    * 
    * @param remitente Usuario que envió el mensaje
    * @param contenido Texto del mensaje
    * @return Mensaje formateado con timestamp
    */
    private String formatearMensaje(String remitente, String contenido) {
        return "[" + new java.text.SimpleDateFormat("HH:mm:ss").format(new Date()) + "] " + remitente + ": "
                + contenido;
    }

    /**
    * Actualiza el contenido del área de chat según el destinatario seleccionado.
    * Muestra mensajes del chat general o de una conversación privada específica.
    */
    private void actualizarAreaChat() {
        // Limpiar área de chat
        areaChat.setText("");
        String destinatario = comboDestinatario.getSelectedItem().toString(); // Obtener destinatario seleccionado

        // Mostrar mensajes según el destinatario
        if ("🌐 Chat General".equals(destinatario)) {
            // Mostrar todos los mensajes del chat general
            for (String msg : mensajesGenerales) {
                areaChat.append(msg + "\n");
            }
        } else {
            // Mostrar conversación privada con usuario específico
            String usuario = destinatario.replace("🔴 ", "").replace("👤 ", "");
            List<String> msgs = mensajesPrivados.getOrDefault(usuario, new ArrayList<>());
            for (String msg : msgs) {
                areaChat.append(msg + "\n");
            }
            // Marcar mensajes como leídos
            usuariosConMensajesNuevos.remove(usuario);
            solicitarUsuarios(); //Refrescar para quitar indicador visual
        }
    }

    
    //Envía un mensaje al destinatario seleccionado usando el protocolo apropiado
    private void enviarMensaje() {
        // Obtener y validar texto del campo de entrada
        String texto = campoMensaje.getText().trim();
        if (texto.isEmpty())
            return;

        // Determinar destinatario y construir comando según protocolo
        String destinatario = comboDestinatario.getSelectedItem().toString();
        if ("🌐 Chat General".equals(destinatario)) {
            // Enviar al chat general: BROADCAST|mensaje
            salida.println("BROADCAST|" + texto);
            mensajesGenerales.add(formatearMensaje("Tú", texto));
        } else {
            // Enviar mensaje privado: MESSAGE|destinatario|mensaje
            String usuario = destinatario.replace("🔴 ", "").replace("👤 ", "");
            salida.println("MESSAGE|" + usuario + "|" + texto);
            mensajesPrivados.computeIfAbsent(usuario, k -> new ArrayList<>())
                    .add(formatearMensaje("Tú", texto));
        }
        // Limpiar campo y actualizar área de chat
        campoMensaje.setText("");
        actualizarAreaChat();
    }

    
    //Solicita al servidor la lista actualizada de usuarios conectados
    private void solicitarUsuarios() {
        if (conectado)
            salida.println("GET_USERS|");
    }

    
    //Solicita al servidor el historial de mensajes del chat general
    private void solicitarHistorial() {
        if (conectado)
            salida.println("GET_HISTORY|");
    }

    /**
    * Muestra una ventana de notificación emergente para mensajes privados nuevos
    * 
    * @param remitente Usuario que envió el mensaje privado
    */
    private void mostrarNotificacionPrivada(String remitente) {
        // Cerrar notificación anterior si existe
        if (ventanaNotificacion != null){
            ventanaNotificacion.dispose();
        }

        // Crear nueva ventana de notificación    
        ventanaNotificacion = new JDialog(ventanaChat, "💬 Nuevo Mensaje", false);
        ventanaNotificacion.setSize(300, 100);
        ventanaNotificacion.setLayout(new BorderLayout());

        //Mensaje de notificación
        JLabel lbl = new JLabel("Nuevo mensaje privado de: " + remitente, SwingConstants.CENTER);
        ventanaNotificacion.add(lbl, BorderLayout.CENTER);

        //Botón para ver el mensaje
        JButton btnVer = new JButton("Ver mensaje");
        btnVer.addActionListener(e -> {
            // Cambiar a la conversación con el remitente
            comboDestinatario.setSelectedItem("👤 " + remitente);
            actualizarAreaChat();
            ventanaNotificacion.dispose();
        });
        ventanaNotificacion.add(btnVer, BorderLayout.SOUTH);

        // Posicionar la notificación en la esquina superior derecha de la ventana principal
        ventanaNotificacion.setLocation(ventanaChat.getX() + ventanaChat.getWidth() - 320,
                ventanaChat.getY() + 50);
        ventanaNotificacion.setVisible(true);

        // Auto-cerrar después de 5 segundos
        new Timer(5000, e -> ventanaNotificacion.dispose()).start();
    }

    /**
    * Muestra una notificación temporal de estado en el panel de usuarios
    * 
    * @param mensaje Texto de la notificación
    * @param color   Color del texto para indicar tipo de evento
    */
    private void mostrarNotificacionTemporal(String mensaje, Color color) {
        labelNotificaciones.setText(mensaje);
        labelNotificaciones.setForeground(color);
        // Auto-limpiar después de 3 segundos
        new Timer(3000, e -> labelNotificaciones.setText(" ")).start();
    }
}