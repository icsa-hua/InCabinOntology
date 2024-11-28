from time_gan_tensorflow.plots import plot 
import pandas as pd 
import numpy as np
import os 
import tensorflow as tf 
import pdb


parent_dir = str(os.getcwd()) 
cleaned_list = parent_dir.split("/")
print("Available GPUs:", tf.config.list_physical_devices('GPU'))
if "Vehicle Ontology" not in cleaned_list: 
    raise ValueError("Please run the script from the Vehicle Ontology folder")

if cleaned_list[-1] != "Vehicle Ontology": 
    parent_dir = "/".join(cleaned_list[:-1])

data_folder = os.path.join(parent_dir, "data/Synthetic_dataset")

test_x = pd.read_csv(data_folder + '/test_x_synthetic_dataset.csv')
x_hat = pd.read_csv(data_folder + '/X_hat_synthetic_dataset.csv')
x_sim = pd.read_csv(data_folder + '/synthetic_dataset.csv')
columns = x_sim.columns
test_x = test_x.to_numpy().astype(int)
x_hat = x_hat.to_numpy().astype(int)
x_sim = x_sim.to_numpy().astype(int)

x = pd.DataFrame(x_sim)
x.columns = columns
x = x.drop(columns=['Unnamed: 0'])
x.to_csv(data_folder+'/Synthetic_dataset_int.csv')

fig = plot(actual=test_x, reconstructed=x_hat, synthetic=x_sim)
fig.write_image(data_folder + '/synthetic_dataset_evaluation.png')

