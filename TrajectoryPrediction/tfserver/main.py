from server import Server
from ai import AI
import os

RESULT_FILE = "logs/training_results.csv"
FILE_VALID_INTERVAL = 15 # 1 = 50s, so 20 is 1000s for the data to be expired.

def starting_print():
    print()
    print("#############################################")
    print("## The tensorflow server is up and running ##")
    print("#############################################")
    print()

def log(message):
    with open(RESULT_FILE, 'a') as f:
        f.write(message)

def get_filenames(ID):
    path = f"logs/{ID}/"
    all_files = []
    max_file_number = 0
    for files in os.listdir(path):
        number = files[4:-4]
        if number.isdigit():
            number = int(number)
            all_files.append((path+files,number))
            if number>max_file_number:
                max_file_number = number
    return [
        files[0]
        for files in all_files
        if files[1] > max_file_number - FILE_VALID_INTERVAL
    ]

def training_sequence(ai: AI, server: Server, dico: dict):
    robot_id = dico['ID']
    weights = dico['weights']
    version = dico['version']
    address = dico['address']
    print(f"training robots {robot_id}'s ({address}) data.")

    # filename = f'{robot_id}/traj.csv'
    filenames = get_filenames(robot_id)

    ai.set_robot_id(robot_id)
    # ai.set_filename(filename)
    ai.set_tf_weights(weights)

    data = ai.load_data(filenames)
    x_train, x_val, y_train, y_val = ai.create_training_and_val_batch(data)
    train_set, val_set = ai.create_datasets(x_train, x_val, y_train, y_val)
    nb_samples_train = len(x_train)
    nb_samples_valid = len(x_val)
    ai.train_model(train_set, val_set, nb_samples_train, nb_samples_valid)

    iteration, loss, val_loss, time = ai.get_history()
    print(f"history of robot {robot_id} : iter:{iteration}, loss:{loss}, val_loss:{val_loss}, time:{time}")
    log(f'{iteration},{robot_id},{address},{version},{nb_samples_train-1},{loss},{val_loss},{time}\n')

    weights = ai.tf_weights_to_list()
    dico = {"nb_samples": nb_samples_train-1, 'weights': weights}
    server.send_message(dico)
    ai.recreate_model()


if __name__ == '__main__':
    server = Server(port=9801)
    ai = AI(0, "")

    with open(RESULT_FILE, 'w') as f:
        f.write('iter,robotID,address,version,nb_samples,loss,val_loss,time\n')

    starting_print()
    running = True
    while running:
        server.accept_new_connection()
        server.send_message({'info': "ready"})
        dico = server.get_message() # the message the client send is only their robot id.

        if 'weights' in  dico:
            training_sequence(ai, server, dico)
        else: 
            running = False
    print("Shutting down the TensorFlow Server.")
        



