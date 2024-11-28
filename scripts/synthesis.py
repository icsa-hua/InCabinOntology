from time_gan_tensorflow.model import TimeGAN
from time_gan_tensorflow.plots import plot
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt 
import os 
import pdb 
import tensorflow as tf
import time 

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def normalize_text(df, column_name): 
    comments = set(df[column_name])
    comm_dict = {comm: i+1 for i, comm in enumerate(comments)}
    return df[column_name].apply(lambda x: comm_dict[x])
    

def main():
    # Get the data from the data folder. 
    parent_dir = str(os.getcwd()) 
    cleaned_list = parent_dir.split("/")
    print("Available GPUs:", tf.config.list_physical_devices('GPU'))
    time.sleep(1)
    if "Vehicle Ontology" not in cleaned_list: 
        raise ValueError("Please run the script from the Vehicle Ontology folder")

    if cleaned_list[-1] != "Vehicle Ontology": 
        parent_dir = "/".join(cleaned_list[:-1])

    data_folder = os.path.join(parent_dir, "data")
    data_filename = "/mental_health_monitoring_dataset.csv"
    data_path = data_folder + data_filename 

    # Read the data from the csv file
    data = pd.read_csv(data_path)

    # Desired Columns 
    columns = ["Timestamp", "Heart_Rate", "Blood_Pressure_Systolic", 
            "Respiration_Rate","Activity_Levels", "Social_Interaction", "Stress_Level", ]

    data = data[columns]
    data["Timestamp"] = pd.to_datetime(data["Timestamp"])
    print(data.describe())

    data.hist(bins=50,figsize=(15,10))
    plt.savefig(data_folder + "/Original_mental_health_monitoring.jpg")

    string_columns = [name for name in data.columns if isinstance(data[name][0],str)]
    for col in string_columns:
        data[col] = normalize_text(data, col)

    

    plt.figure(2)
    plt.matshow(data.corr())
    plt.savefig(data_folder + "/Correlation_mental_health_monitoring.jpg")

    data.to_csv(data_folder + "/processed_mental_health_monitoring_data.csv")
    data.drop(columns=["Timestamp"], inplace=True)
    # data = data['Heart_Rate']
    # data = data.to_numpy()
    #Data Generation 
    train_x, test_x = data[:int(0.6*len(data))], data[int(0.6*len(data)):]

    model = TimeGAN(
        x=train_x,
        timesteps=60,
        hidden_dim=64,
        num_layers=3,
        lambda_param=0.1,
        eta_param=10,
        learning_rate=0.001,
        batch_size=64
    )
    model.fit(
        epochs=500,
        verbose=False
    )

    x_hat = model.reconstruct(x=test_x)
    x_sim = model.simulate(samples=len(test_x))

    test_x = test_x.to_numpy()
    x_hat = x_hat.to_numpy()
    x_sim = x_sim.to_numpy()

    fig = plot(actual=test_x, reconstructed=x_hat, synthetic=x_sim)
    fig.write_image(data_folder + "/synthetic_mental_health_monitoring_data.jpg", scale=4, height=900, width=700)
    

if __name__ == "__main__":
    # Inputs for the main function   
  main()
