# Neural Network parameters
params = {}
params['EMBEDDING_SIZE'] = 16
params['NUM_OUTPUTS'] = 2
params['SEQ_LENGTH'] = 32
params['DIM_INPUT'] = 2
params['DROPOUT'] = 0.2
params['sample_shape'] = (params['SEQ_LENGTH'] , params['DIM_INPUT'])

# Generic training parameters
params['TRAIN_RATIO'] = 0.8
params['VAL_RATIO'] =  1 - params['TRAIN_RATIO']
params['PAST_HISTORY'] = 32
params['FUTURE_TARGET'] = 48

# Centralized training parameters
params['BATCH_SIZE_C'] = 256
params['BUFFER_SIZE_C'] = 10000 # just keep a big value for perfect shuffeling
params['EVALUATION_INTERVAL_C'] = 50
params['EPOCHS_C'] = 150  #going to be overridden
params['VALIDATION_STEPS_C']= 50

# FL training parameters
# Generic
params['EXP_DURATION'] = 50000
params['LOCAL_EPOCHS'] = 1
params['LOCAL_BATCH'] = 20