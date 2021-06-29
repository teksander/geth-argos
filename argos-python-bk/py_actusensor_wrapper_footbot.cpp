#include "py_actusensor_wrapper_footbot.h"
#include "py_wrapper.h"

using namespace argos;

/****************************************/
/****************************************/

CGripperWrapper::CGripperWrapper()
{
}

void CGripperWrapper::Lock()
{
    if (m_bGripper)
    {
        m_pcGripper->LockPositive();
    }
    else
    {
        ActusensorsWrapper::Logprint("Gripper Actuator not implemented or not stated in XML config.");
    }
}
void CGripperWrapper::Unlock()
{
    if (m_bGripper)
    {
        m_pcGripper->Unlock();
    }
    else
    {
        ActusensorsWrapper::Logprint("Gripper Actuator not implemented or not stated in XML config.");
    }
}

/****************************************/
/****************************************/

CFootBotProximitySensorWrapper::CFootBotProximitySensorWrapper()
{
}

boost::python::list CFootBotProximitySensorWrapper::GetReadings() const
{
    if (m_bProximity)
    {
        return ActusensorsWrapper::ToPythonList(m_pcProximity->GetReadings());
    }
    else
    {
        ActusensorsWrapper::Logprint("Proximity sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/
CGroundSensorWrapper::CGroundSensorWrapper()
{
}

boost::python::list CGroundSensorWrapper::GetReadings() const
{
    if (m_bGround)
    {
        return ActusensorsWrapper::ToPythonList(m_pcGround->GetReadings());
    }
    else
    {
        ActusensorsWrapper::Logprint("Motor Ground Sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/

CBaseGroundSensorWrapper::CBaseGroundSensorWrapper()
{
}

boost::python::list CBaseGroundSensorWrapper::GetReadings() const
{
    if (m_bBaseGround)
    {
        return ActusensorsWrapper::ToPythonList(m_pcBaseGround->GetReadings());
    }
    else
    {
        ActusensorsWrapper::Logprint("Base Ground Sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/

CLightSensorWrapper::CLightSensorWrapper()
{
}

boost::python::list CLightSensorWrapper::GetReadings() const
{
    if (m_bLight)
    {
        return ActusensorsWrapper::ToPythonList(m_pcLight->GetReadings());
    }
    else
    {
        ActusensorsWrapper::Logprint("Light Sensor not implemented or not stated in XML config.");
        // TODO: add exception?
    }
}

/****************************************/
/****************************************/

CDistanceScannerWrapper::CDistanceScannerWrapper()
{
}

void CDistanceScannerWrapper::Enable()
{
    if (m_bScannerActuator)
    {
        m_pcScannerActuator->Enable();
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Actuator not implemented or not stated in XML config.");
    }
}

void CDistanceScannerWrapper::Disable()
{
    if (m_bScannerActuator)
    {
        m_pcScannerActuator->Disable();
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Actuator not implemented or not stated in XML config.");
    }
}

void CDistanceScannerWrapper::SetRPM(const Real f_rpm)
{
    if (m_bScannerActuator)
    {
        if (f_rpm < 0)
            m_pcScannerActuator->SetRPM(0);
        m_pcScannerActuator->SetRPM(f_rpm);
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Actuator not implemented or not stated in XML config.");
    }
}

void CDistanceScannerWrapper::SetAngle(const Real f_angle)
{
    if (m_bScannerActuator)
    {
        m_pcScannerActuator->SetAngle(CRadians(f_angle));
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Actuator not implemented or not stated in XML config.");
    }
}

std::map<CRadians, Real> CDistanceScannerWrapper::GetReadings() const
{
    if (m_bScannerSensor)
    {
        return m_pcScannerSensor->GetReadingsMap();
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Sensor not implemented or not stated in XML config.");
    }
}

std::map<CRadians, Real> CDistanceScannerWrapper::GetShortReadings() const
{
    if (m_bScannerSensor)
    {
        return m_pcScannerSensor->GetShortReadingsMap();
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Sensor not implemented or not stated in XML config.");
    }
}

std::map<CRadians, Real> CDistanceScannerWrapper::GetLongReadings() const
{
    if (m_bScannerSensor)
    {
        return m_pcScannerSensor->GetLongReadingsMap();
    }
    else
    {
        ActusensorsWrapper::Logprint("Distance Scanner Sensor not implemented or not stated in XML config.");
    }
}

/****************************************/
/****************************************/

CTurretWrapper::CTurretWrapper()
{
}

CRadians CTurretWrapper::GetRotation() const
{
    if (m_bTurretSensor)
    {
        return m_pcTurretSensor->GetRotation();
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Sensor not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetRotation(const Real f_angle)
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetRotation(argos::CRadians(f_angle));
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetRotationSpeed(const UInt32 n_speed_pulses)
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetRotationSpeed(n_speed_pulses);
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetMode(const std::string str_mode_name)
{
    if (m_bTurretActuator)
    {
        if (str_mode_name == "off")
        {
            m_pcTurretActuator->SetMode(argos::CCI_FootBotTurretActuator::ETurretModes::MODE_OFF);
        }
        if (str_mode_name == "passive")
        {
            m_pcTurretActuator->SetMode(argos::CCI_FootBotTurretActuator::ETurretModes::MODE_PASSIVE);
        }
        if (str_mode_name == "speed_control")
        {
            m_pcTurretActuator->SetMode(argos::CCI_FootBotTurretActuator::ETurretModes::MODE_SPEED_CONTROL);
        }
        if (str_mode_name == "position_control")
        {
            m_pcTurretActuator->SetMode(argos::CCI_FootBotTurretActuator::ETurretModes::MODE_POSITION_CONTROL);
        }
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetActiveWithRotation(const Real f_angle)
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetActiveWithRotation(argos::CRadians(f_angle));
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetSpeedControlMode()
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetSpeedControlMode();
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetPositionControlMode()
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetPositionControlMode();
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}

void CTurretWrapper::SetPassiveMode()
{
    if (m_bTurretActuator)
    {
        m_pcTurretActuator->SetPassiveMode();
    }
    else
    {
        ActusensorsWrapper::Logprint("Turret Actuator not implemented or not stated in XML config.");
    }
}