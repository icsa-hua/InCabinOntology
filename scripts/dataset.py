import numpy as np 
import pandas as pd 
import pdb 
import random

csv = pd.read_csv("../data/Synthetic_dataset/data_SAT_20240603.csv")

columns_to_add = ['Demographic','Age','Sex','Accessories','Characteristics']
drowsy = [1,2,3,4]
demographic = ["Afghan", "Brazilian", "African", "American", "Austrian", "Canadian", "Czech", "German", "Japanese", "Mexican", "Swedish"]
ages = [15,18, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
sexes = ["Man", "Woman"]
accessories = ["Glasses", "Scarf", "Hat"]
characteristics = ["Grey_hair", "Long_hair", "Short_hair", "Beard"]
drowsy = np.array([random.choice(drowsy) for _ in range(len(csv))]).reshape(-1,1)
demo = np.array([random.choice(demographic) for _ in range(len(csv))]).reshape(-1,1)
ages = np.array([random.choice(ages) for _ in range(len(csv))]).reshape(-1,1)
sexes = np.array([random.choice(sexes) for _ in range(len(csv))]).reshape(-1,1)
accessories = np.array([random.choice(accessories) for _ in range(len(csv))]).reshape(-1,1)
characteristics = np.array([random.choice(characteristics) for _ in range(len(csv))]).reshape(-1,1)
hrv = np.array([random.randint(20,200) for _ in range(len(csv))]).reshape(-1,1)
csv['HRV'] = hrv 
csv['DROWSY'] = drowsy
csv_pd = np.hstack([demo, ages, sexes, accessories, characteristics])
csv_pd = pd.DataFrame(csv_pd, columns=columns_to_add)

try: 
    final = pd.concat([csv, csv_pd], axis=1)
    final.dropna(inplace=True)
    final.to_csv("../data/Synthetic_dataset/test_set_ontology.csv", index=False)               
    print("Dataset saved successfully!")
except  Exception as e:
    print(e)