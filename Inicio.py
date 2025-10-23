import streamlit as st
import paho.mqtt.client as mqtt
import json
import time


st.set_page_config(
    page_title="Lector de Sensor MQTT",
    page_icon="📡",
    layout="centered"
)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función para obtener un mensaje MQTT """
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except:
            # Si no es JSON, guardar como texto
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True
    
    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        # Esperar máximo 5 segundos
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración
with st.sidebar:
    st.subheader('⚙️ Configuración de Conexión')
    
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com', 
                           help='Dirección del broker MQTT')
    
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535,
                           help='Puerto del broker (generalmente 1883)')
    
    topic = st.text_input('Tópico', value='sensor_st',
                          help='Tópico MQTT a suscribirse')
    
    client_id = st.text_input('ID del Cliente', value='streamlit_client',
                              help='Identificador único para este cliente')

# Título
st.title('📡 Lector de Sensor MQTT')

# Información al inicio
with st.expander('ℹ️ Información', expanded=False):
    st.markdown("""
    ### Cómo usar esta aplicación:
    
    1. **Broker MQTT**: Ingresa la dirección del servidor MQTT en el sidebar
    2. **Puerto**: Generalmente es 1883 para conexiones no seguras
    3. **Tópico**: El canal al que deseas suscribirte
    4. **ID del Cliente**: Un identificador único para esta conexión
    5. Haz clic en **Obtener Datos** para recibir el mensaje más reciente
    
    ### Brokers públicos para pruebas:
    - broker.mqttdashboard.com
    - test.mosquitto.org
    - broker.hivemq.com
    """)

st.divider()

# Botón para obtener datos
if st.button('Obtener Datos del Sensor', use_container_width=True):
    with st.spinner('Conectando - Esperando datos...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Mostrar resultados
if st.session_state.sensor_data:
    st.divider()
    st.subheader('Datos Recibidos')
    
    data = st.session_state.sensor_data
    
    # Verificar si hay error
    if isinstance(data, dict) and 'error' in data:
        st.error(f"ERROR de conexion: {data['error']}")
    else:
        st.success('Los datos se recibieron correctamente!')
        
        # Mostrar datos en formato JSON
        if isinstance(data, dict):
            # Mostrar cada campo en una métrica
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=key, value=value)
            
            # Mostrar JSON completo
            with st.expander('Ver JSON completo'):
                st.json(data)
        else:
            # Si no es diccionario, mostrar como texto
            st.code(data)
