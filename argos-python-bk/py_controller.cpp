/*
 * AUTHOR: Ken Hasselmann <arg AT kenh DOT fr>
 *
 * Connects ARGoS to python
 *
 */
#include "py_controller.h"

using namespace argos;
using namespace boost::python;

#if PY_MAJOR_VERSION >= 3
#   define INIT_MODULE PyInit_libpy_controller_interface
    extern "C" PyObject* INIT_MODULE();
#else
#   define INIT_MODULE initlibpy_controller_interface
    extern "C" void INIT_MODULE();
#endif


CPyController::CPyController() :
  m_actusensors(NULL),
  m_main(NULL),
  m_namesp(NULL),
  m_script(NULL),
  m_interpreter(NULL)
{
  //init python
  PyImport_AppendInittab((char*)"libpy_controller_interface", INIT_MODULE);
  if (!Py_IsInitialized())
  {
      Py_Initialize();
  }
  m_interpreter = Py_NewInterpreter();
  //init main module and namespace
  m_main = import("__main__");
  m_namesp = m_main.attr("__dict__");

}

void CPyController::Destroy() {
  //launch python destroy function
  try
  {
    object destroy = m_main.attr("destroy");
    destroy();
  }
    catch (error_already_set)
  {
    PyErr_Print();
  }
  //Py_EndInterpreter(m_interpreter);
  //Py_Finalize(); //the documentation of boost says we should NOT use this ..
}

void CPyController::Reset() {
  //launch python reset function
  try
  {
    object reset_f = m_main.attr("reset");
    reset_f();
  }
  catch (error_already_set)
  {
    PyErr_Print();
  }
}

// TODO: PASS TNODE
void CPyController::InitSensorsActuators(TConfigurationNode& t_node)
{
  for(CCI_Actuator::TMap::iterator it = m_mapActuators.begin();
      it != m_mapActuators.end();
      ++it)
  {
    m_actusensors->CreateActu(it->first, it->second, t_node); //this);
  }

  for(CCI_Sensor::TMap::iterator it = m_mapSensors.begin();
      it != m_mapSensors.end();
      ++it)
  {
     m_actusensors->CreateSensor(it->first, it->second, t_node);
  }

}

void CPyController::Init(TConfigurationNode& t_node)
{
  //get instances of actuators and sensors and pass them to the wrapper
  m_actusensors = boost::make_shared< ActusensorsWrapper >();
  //m_actusensors = new ActusensorsWrapper();
  InitSensorsActuators(t_node);
  //printf("%s\n", this);

  /* Load script */
  std::string strScriptFileName;
  GetNodeAttributeOrDefault(t_node, "script", strScriptFileName, strScriptFileName);
  if(strScriptFileName == "")
  {
    THROW_ARGOSEXCEPTION("Error loading python script \"" << strScriptFileName << "\"" << std::endl);
  }
  //exec user script
  try 
  {
	  m_script = exec_file(strScriptFileName.c_str(), m_namesp, m_namesp);
		  
	  // std::cout << "strScript:" << strScriptFileName << std::endl;
	  // std::cout << GetId().c_str() << std::endl;
	  }
    
  catch(error_already_set)
  {
	  PyErr_Print();
  }
  
  try
  {
    //import the wrappers's lib
    PyRun_SimpleString("import libpy_controller_interface as lib");
    object lib = import("libpy_controller_interface");
    m_namesp["robot"] = m_actusensors;
    //m_namesp["robot"] = ptr(m_actusensors);

    //launch python init function
    object init_f = m_main.attr("init");
    init_f();
  }
  catch (error_already_set)
  {
    PyErr_Print();
  }

}

void CPyController::ControlStep()
{
  //here the sensors should be updated every step


  //launch controlstep python function*
  try
  {
    object controlstep = m_main.attr("controlstep");
    controlstep();
  }
    catch (error_already_set)
  {
    PyErr_Print();
  }
}

REGISTER_CONTROLLER(CPyController, "python_controller");
