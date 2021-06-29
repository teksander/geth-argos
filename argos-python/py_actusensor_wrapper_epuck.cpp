#include "py_actusensor_wrapper_epuck.h"
#include "py_wrapper.h"

using namespace argos;

/****************************************/
/****************************************/

CEPuckWheelsWrapper::CEPuckWheelsWrapper() {}

void CEPuckWheelsWrapper::SetSpeed(const Real f_left_wheel_speed, const Real f_right_wheel_speed) {
    if (m_pcEPuckWheels == nullptr) {
        ActusensorsWrapper::Logprint(
            "Differential Steering Actuator not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckWheels->SetLinearVelocity(f_left_wheel_speed, f_right_wheel_speed);
}

/****************************************/
/****************************************/

CIdWrapper::CIdWrapper() {}

const std::string CIdWrapper::GetId() {
    return m_cId;
}

void CIdWrapper::SetId(const std::string id) {
    m_cId = id;
}



CEPuckProximitySensorWrapper::CEPuckProximitySensorWrapper() {}

boost::python::list CEPuckProximitySensorWrapper::GetReadings() const {
    if (m_pcEPuckProximity == nullptr) {
        ActusensorsWrapper::Logprint(
            "Proximity sensor not implemented or not stated in XML config.");
        // TODO: add exception?
        return {};
    }
    return ActusensorsWrapper::ToPythonList(m_pcEPuckProximity->GetReadings());
}

/****************************************/
/****************************************/

CEPuckGroundSensorWrapper::CEPuckGroundSensorWrapper() {}

argos::CCI_EPuckGroundSensor::SReadings CEPuckGroundSensorWrapper::GetReadings() const {
    if (m_pcEPuckGround == nullptr) {
        ActusensorsWrapper::Logprint(
            "Motor Ground Sensor not implemented or not stated in XML config.");
        // TODO: add exception?
        return {};
    }
    return m_pcEPuckGround->GetReadings();
}

/****************************************/
/****************************************/

CEPuckRangeAndBearingWrapper::CEPuckRangeAndBearingWrapper() {}

void CEPuckRangeAndBearingWrapper::ClearPackets() {
    if (m_pcEPuckRABS == nullptr) {
        ActusensorsWrapper::Logprint("RABS not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckRABS->ClearPackets();
}
// Send a buffer to all the emitters.
void CEPuckRangeAndBearingWrapper::SetData(const boost::python::list un_data) {
    if (m_pcEPuckRABA == nullptr) {
        ActusensorsWrapper::Logprint("RABA not implemented or not stated in XML config.");
        return;
    }
    /* std::cout << "rab da:" << un_data << std::endl; */
    const UInt8 unData[argos::CCI_EPuckRangeAndBearingActuator::MAX_BYTES_SENT] =
         {boost::python::extract<UInt8>(boost::python::object(un_data[0])),
          boost::python::extract<UInt8>(boost::python::object(un_data[1])),
          boost::python::extract<UInt8>(boost::python::object(un_data[2])),
          boost::python::extract<UInt8>(boost::python::object(un_data[3]))};
    //const UInt8 unData[3] = {0, 0, 0};
    std::cout << m_pcEPuckRABA << "raba" << std::endl;
    m_pcEPuckRABA->SetData(unData);
}
// TODO: Set all bits at once
// Return the readings obtained at this control step.
// Each reading contains the range, the horizontal bearing, the vertical bearing and the data table.
// The data table is exposed as a c_byte_array.
boost::python::list CEPuckRangeAndBearingWrapper::GetPackets() const {
    if (m_pcEPuckRABS == nullptr) {
        ActusensorsWrapper::Logprint("RABS not implemented or not stated in XML config.");
        return {};
    }


    boost::python::list outerList;

    for (size_t i = 0; i < m_pcEPuckRABS->GetPackets().size(); ++i) {
        boost::python::list innerList;    

        for (size_t j = 0; j < sizeof(m_pcEPuckRABS->GetPackets()[i]->Data)/sizeof(*m_pcEPuckRABS->GetPackets()[i]->Data); ++j) {
            innerList.append((int) m_pcEPuckRABS->GetPackets()[i]->Data[j]);
        }
    // Extract range: m_pcEPuckRABS->GetPackets()[i]->Range
    innerList.append(m_pcEPuckRABS->GetPackets()[i]->Range);
    //innerList.append(m_pcEPuckRABS->GetPackets()[i]->Bearing);
    //innerList.append(m_pcEPuckRABS->GetPackets()[i]->VerticalBearing);

    outerList.append(innerList);
    }

    return outerList;
}

/****************************************/
/****************************************/

CEPuckLedsActuatorWrapper::CEPuckLedsActuatorWrapper() {}

// Set the color of a given led, given its name.
void CEPuckLedsActuatorWrapper::SetSingleColorString(const UInt8 un_led_id,
                                                     const std::string str_color_name) {
    if (m_pcEPuckLeds == nullptr) {
        ActusensorsWrapper::Logprint("Leds not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckLeds->SetColor(un_led_id, ActusensorsWrapper::CColorWrapper(str_color_name).m_cColor);
}
// Set the color of a given led, given its RGB values.
void CEPuckLedsActuatorWrapper::SetSingleColorRGB(const UInt8 un_led_id, const UInt8 un_red,
                                                  const UInt8 un_green, const UInt8 un_blue) {
    if (m_pcEPuckLeds == nullptr) {
        ActusensorsWrapper::Logprint("Leds not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckLeds->SetColor(un_led_id,
                            ActusensorsWrapper::CColorWrapper(un_red, un_green, un_blue).m_cColor);
}
// Set the color of every led, given its name.
void CEPuckLedsActuatorWrapper::SetAllColorsString(const std::string str_color_name) {
    if (m_pcEPuckLeds == nullptr) {
        ActusensorsWrapper::Logprint("Leds not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckLeds->SetColors(ActusensorsWrapper::CColorWrapper(str_color_name).m_cColor);
}
// Set the color of every led, given its RGB values.
void CEPuckLedsActuatorWrapper::SetAllColorsRGB(const UInt8 un_red, const UInt8 un_green,
                                                const UInt8 un_blue) {
    if (m_pcEPuckLeds == nullptr) {
        ActusensorsWrapper::Logprint("Leds not implemented or not stated in XML config.");
        return;
    }
    m_pcEPuckLeds->SetColors(ActusensorsWrapper::CColorWrapper(un_red, un_green, un_blue).m_cColor);
}
