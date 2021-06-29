#include "py_actusensor_wrapper_epuck.h"
#include "py_wrapper.h"

using namespace argos;

/****************************************/
/****************************************/

CEPuckWheelsWrapper::CEPuckWheelsWrapper()
{
}

void CEPuckWheelsWrapper::SetSpeed(const Real f_left_wheel_speed, const Real f_right_wheel_speed)
{
    if (m_bEPuckWheels)
    {
        m_pcEPuckWheels->SetLinearVelocity(f_left_wheel_speed, f_right_wheel_speed);
    }
    else
    {
        ActusensorsWrapper::Logprint("Differential Steering Actuator not implemented or not stated in XML config.");
    }
}

/****************************************/
/****************************************/

CEPuckProximitySensorWrapper::CEPuckProximitySensorWrapper()
{
}

boost::python::list CEPuckProximitySensorWrapper::GetReadings() const
{
    if (m_bEPuckProximity)
    {
        return ActusensorsWrapper::ToPythonList(m_pcEPuckProximity->GetReadings());
    }
    else
    {
        ActusensorsWrapper::Logprint("Proximity sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/

CEPuckGroundSensorWrapper::CEPuckGroundSensorWrapper()
{
}

argos::CCI_EPuckGroundSensor::SReadings CEPuckGroundSensorWrapper::GetReadings() const
{
    if (m_bEPuckGround)
    {
        return m_pcEPuckGround->GetReadings();
    }
    else
    {
        ActusensorsWrapper::Logprint("Motor Ground Sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/

CEPuckRangeAndBearingWrapper::CEPuckRangeAndBearingWrapper()
{
}

void CEPuckRangeAndBearingWrapper::ClearPackets()
{
    m_pcEPuckRABS->ClearPackets();
}
// Send a buffer to all the emitters.
void CEPuckRangeAndBearingWrapper::SetData(const boost::python::list un_data)
{
    const UInt8 unData[argos::CCI_EPuckRangeAndBearingActuator::MAX_BYTES_SENT] = 
        {boost::python::extract<UInt8>(boost::python::object(un_data[0])),
         boost::python::extract<UInt8>(boost::python::object(un_data[1])), 
         boost::python::extract<UInt8>(boost::python::object(un_data[2])), 
         boost::python::extract<UInt8>(boost::python::object(un_data[3]))};
    m_pcEPuckRABA->SetData(unData);
}
// TODO: Set all bits at once
// Return the readings obtained at this control step.
// Each reading contains the range, the horizontal bearing, the vertical bearing and the data table.
// The data table is exposed as a c_byte_array.
boost::python::list CEPuckRangeAndBearingWrapper::GetPackets() const
{

    boost::python::list list;

    list.append(m_pcEPuckRABS->GetPackets()[0]->Data[0]);


    return list;
}


/****************************************/
/****************************************/

CEPuckLedsActuatorWrapper::CEPuckLedsActuatorWrapper()
{
}

// Set the color of a given led, given its name.
void CEPuckLedsActuatorWrapper::SetSingleColorString(const UInt8 un_led_id, const std::string str_color_name)
{
    m_pcEPuckLeds->SetColor(un_led_id, ActusensorsWrapper::CColorWrapper(str_color_name).m_cColor);
}
// Set the color of a given led, given its RGB values.
void CEPuckLedsActuatorWrapper::SetSingleColorRGB(const UInt8 un_led_id, const UInt8 un_red, const UInt8 un_green, const UInt8 un_blue)
{
    m_pcEPuckLeds->SetColor(un_led_id, ActusensorsWrapper::CColorWrapper(un_red, un_green, un_blue).m_cColor);
}
// Set the color of every led, given its name.
void CEPuckLedsActuatorWrapper::SetAllColorsString(const std::string str_color_name)
{
    m_pcEPuckLeds->SetColors(ActusensorsWrapper::CColorWrapper(str_color_name).m_cColor);
}
// Set the color of every led, given its RGB values.
void CEPuckLedsActuatorWrapper::SetAllColorsRGB(const UInt8 un_red, const UInt8 un_green, const UInt8 un_blue)
{
    m_pcEPuckLeds->SetColors(ActusensorsWrapper::CColorWrapper(un_red, un_green, un_blue).m_cColor);
}