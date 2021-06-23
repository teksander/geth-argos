#ifndef PY_ACTUSENSOR_WRAPPER_GENERIC_H
#define PY_ACTUSENSOR_WRAPPER_GENERIC_H

#include <boost/python.hpp>
#include <boost/python/suite/indexing/map_indexing_suite.hpp>

#include <argos3/core/control_interface/ci_controller.h>

#include <argos3/plugins/robots/generic/control_interface/ci_differential_steering_actuator.h>
#include <argos3/plugins/robots/generic/control_interface/ci_colored_blob_omnidirectional_camera_sensor.h>
#include <argos3/plugins/robots/generic/control_interface/ci_leds_actuator.h>
/* Definition of the range and bearing actuator */
#include <argos3/plugins/robots/generic/control_interface/ci_range_and_bearing_actuator.h>
/* Definition of the range and bearing sensor */
#include <argos3/plugins/robots/generic/control_interface/ci_range_and_bearing_sensor.h>

#include <argos3/core/utility/logging/argos_log.h>
#include <argos3/core/utility/math/general.h>

#include <string>
#include <iostream>

namespace argos
{
// For each actuator and sensor, it is provided a struct that contains a reference to the actual C++ actuator or sensor,
// and a series of functions to interact with it.
// Each wrapper is then exported in python as a property of the "robot" class,
// and the functions of each wrapper can be used from python as methods or class properties

// TODO: add m_pc_..._bool error checkin
// Wrapper for the Differential Steering Actuator.
class CWheelsWrapper
{
  public:
    CWheelsWrapper();
    ~CWheelsWrapper(){};
    argos::CCI_DifferentialSteeringActuator *m_pcWheels;
    bool m_bWheels;
    // Set the speed of the two wheels.
    void SetSpeed(const Real f_left_wheel_speed, const Real f_right_wheel_speed);
};

/****************************************/
/****************************************/

// Wrapper for the Omnidirectional Camera.
// It is possible to enable/disable the camera, get the number of readings, and get the readings of the camera.
class COmnidirectionalCameraWrapper
{
  public:
    COmnidirectionalCameraWrapper();
    ~COmnidirectionalCameraWrapper(){};
    argos::CCI_ColoredBlobOmnidirectionalCameraSensor *m_pcOmniCam;
    bool m_bOmniCam;
    // Get the readings from the camera, obtained at this control step.
    // Each reading is exposed as a "omnidirectional_camera_packet",
    // from which it is possible to obtain distance, angle and color of each reading.
    boost::python::list GetReadings() const;

    // Enable the camera.
    void Enable();

    // Disable the camera.
    void Disable();

    // Return the number of readings obtained so far, i.e. the number of control steps from which the recording started.
    const int GetCounter() const;
};

/****************************************/
/****************************************/
// Wrapper for the Range and Bearing Sensor and Actuator.
// Both of them are exposed as a single property of the robot, for simplicity.
class CRangeAndBearingWrapper
{
  public:
    CRangeAndBearingWrapper();
    ~CRangeAndBearingWrapper(){};

    argos::CCI_RangeAndBearingActuator *m_pcRABA;
    argos::CCI_RangeAndBearingSensor *m_pcRABS;
    bool m_bRABA;
    bool m_bRABS;
    // Erase the readings.
    void ClearData();
    // Set the i-th bit of the data table.
    void SetData(const size_t un_idx, const UInt8 un_value);
    // TODO: Set all bits at once
    // Return the readings obtained at this control step.
    // Each reading contains the range, the horizontal bearing, the vertical bearing and the data table.
    // The data table is exposed as a c_byte_array.
    boost::python::list GetReadings() const;
};

/****************************************/
/****************************************/

// Wrapper for the Leds Actuator.
class CLedsActuatorWrapper
{
  public:
    CLedsActuatorWrapper();
    ~CLedsActuatorWrapper(){};

    argos::CCI_LEDsActuator *m_pcLeds;
    bool m_bLeds;

    // Set the color of a given led, given its name.
    void SetSingleColorString(const UInt8 un_led_id, const std::string str_color_name);

    // Set the color of a given led, given its RGB values.
    void SetSingleColorRGB(const UInt8 un_led_id, const UInt8 un_red, const UInt8 un_green, const UInt8 un_blue);

    // Set the color of every led, given its name.
    void SetAllColorsString(const std::string str_color_name);

    // Set the color of every led, given its RGB values.
    void SetAllColorsRGB(const UInt8 un_red, const UInt8 un_green, const UInt8 un_blue);
};
}

#endif
