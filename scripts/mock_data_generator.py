import numpy as np
import random

class MockDataGenerator:
    def __init__(self, num_samples=100):
        self.num_samples = num_samples  # Number of data samples to generate 

    def generate_normal_distribution(self, mean, std_dev):
        """
        General function to generate data based on a normal distribution.
        """
        return np.random.normal(mean, std_dev, self.num_samples)

    def generate_resp_rate_by_age(self, age_group):
        """
        Function to generate synthetic data for respiratory rate based on age group.
        """
        if age_group == "birth_6_weeks":
            return self.generate_normal_distribution(35, 2.5)
        elif age_group == "6_months":
            return self.generate_normal_distribution(32.5, 2.5)
        elif age_group == "3_years":
            return self.generate_normal_distribution(25, 2.5)
        elif age_group == "6_years":
            return self.generate_normal_distribution(21.5, 2)
        elif age_group == "10_years":
            return self.generate_normal_distribution(20, 1.5)
        elif age_group == "adults":
            return self.generate_normal_distribution(16.5, 1)
        elif age_group == "50_years":
            return self.generate_normal_distribution(21.5, 2)
        elif age_group == "elderly_65":
            return self.generate_normal_distribution(20, 4)
        elif age_group == "elderly_80":
            return self.generate_normal_distribution(20, 5)
        else:
            raise ValueError("Invalid age group for respiratory rate")

    def generate_heart_rate_by_age(self, age):
        """
        Function to generate synthetic data for heart rate based on age.
        """
        age_hr_ranges = {
            (1,20): (135, 35),  # Mean: (100 + 170) / 2 = 135, Std Dev: (170 - 100) / 6 ≈ 35
            (21,30): (128.5, 33.5),  # Mean: (95 + 162) / 2 = 128.5, Std Dev: (162 - 95) / 6 ≈ 33.5
            (31,35): (125, 32),  # Mean: (93 + 157) / 2 = 125, Std Dev: (157 - 93) / 6 ≈ 32
            (36,40): (121.5, 30),  # Mean: (90 + 153) / 2 = 121.5, Std Dev: (153 - 90) / 6 ≈ 30
            (41,45): (118.5, 28),  # Mean: (88 + 149) / 2 = 118.5, Std Dev: (149 - 88) / 6 ≈ 28
            (46,50): (115, 27.5),  # Mean: (85 + 145) / 2 = 115, Std Dev: (145 - 85) / 6 ≈ 27.5
            (51,55): (111.5, 26),  # Mean: (83 + 140) / 2 = 111.5, Std Dev: (140 - 83) / 6 ≈ 26
            (56,60): (108, 25),  # Mean: (80 + 136) / 2 = 108, Std Dev: (136 - 80) / 6 ≈ 25
            (61,65): (104, 23.5),  # Mean: (78 + 132) / 2 = 105, Std Dev: (132 - 78) / 6 ≈ 23.5
            (66,70): (101.5, 22),  # Mean: (75 + 128) / 2 = 101.5, Std Dev: (128 - 75) / 6 ≈ 22
            (71,140): (101.5, 22)
        }
        index_position = self.find_range_value(age, age_hr_ranges)
        if index_position is not None:
            mean, std_dev = age_hr_ranges[index_position]
            return self.generate_normal_distribution(mean, std_dev)
        else:
            raise ValueError("Invalid age for heart rate")

    def generate_hrv_by_age(self, age):
        """
        Function to generate synthetic data for heart rate variability based on age.
        """
        age_hrv_ranges = {
            (1,20): (85, 12.5),
            (21,25): (76, 10.5),
            (26,30): (67.5, 9),
            (31,35): (57, 7),
            (36,40): (50, 6),
            (41,45): (46, 5.5),
            (46,50): (43, 5),
            (51,55): (41.5, 4.5),
            (56,60): (39.5, 4.5),
            (61,65): (40, 5),
            (66,140): (40, 5)
        }
        index_position = self.find_range_value(age, age_hrv_ranges)
        if index_position is not None:
            mean, std_dev = age_hrv_ranges[index_position]
            return self.generate_normal_distribution(mean, std_dev)
        else:
            raise ValueError("Invalid age for heart rate variability")


    def generate_attention_levels(self):
        """
        Function to generate synthetic data for driver attention levels.
        The attention level ranges from 1 to 5.
        """
        levels = self.generate_normal_distribution(mean=3, std_dev=1)
        return np.clip(np.round(levels), 1, 5)  # Ensures values are between 1 and 5


    def generate_blood_saturation_levels(self):
        """
        Function to generate synthetic data for blood saturation levels.
        Based on the provided ranges.
        """
        levels = []
        for _ in range(self.num_samples):
            rand = random.random()
            if rand < 0.10:  # 10% chance for < 88%
                levels.append(random.uniform(80, 88))  # Dangerously low
            elif rand < 0.30:  # 20% chance for 89% - 92%
                levels.append(random.uniform(89, 92))  # Low value, should contact medical staff
            elif rand < 0.60:  # 30% chance for ~90% - normal for some patients
                levels.append(random.uniform(90, 92))  # Some chronic conditions
            elif rand < 0.90:  # 30% chance for 92% - 95%
                levels.append(random.uniform(92, 95))  # Borderline ok
            else:  # 10% chance for > 95%
                levels.append(random.uniform(95, 100))  # Normal state
        return np.clip(levels, 80, 100)  # Clipping to ensure valid saturation levels


    def generate_fatigue_scores(self):
        """
        Function to generate synthetic data for FAID and FAST scores.
        FAID values can be generated between 0 to 100 (for simplicity).
        FAST values can also be generated similarly.
        """
        faid_scores = self.generate_normal_distribution(mean=60, std_dev=15)
        fast_scores = self.generate_normal_distribution(mean=75, std_dev=15)

        return np.clip(faid_scores, 0, 100), np.clip(fast_scores, 0, 100)


    def classify_fatigue_levels(self, faid, fast):
        """
        Classifies the fatigue level based on FAID and FAST scores.
        Returns a list of fatigue levels.
        """
        fatigue_levels = []
        for f, s in zip(faid, fast):
            if f > 80 and s < 50:
                fatigue_levels.append("Severely Fatigued")
            elif f > 70 and s < 60:
                fatigue_levels.append("Extremely Fatigued")
            elif f > 60 and s < 70:
                fatigue_levels.append("Very Fatigued")
            elif f > 50 and s < 80:
                fatigue_levels.append("Moderately Fatigued")
            elif f > 40 and s < 90:
                fatigue_levels.append("Fatigued")
            else:
                fatigue_levels.append("Not Fatigued")
        return fatigue_levels


    def simulate_fatigue(self):
        """
        Simulates fatigue levels based on FAID and FAST scores.
        Returns FAID scores, FAST scores, and corresponding fatigue levels.
        """
        faid_scores, fast_scores = self.generate_fatigue_scores()
        fatigue_levels = self.classify_fatigue_levels(faid_scores, fast_scores)
        return faid_scores, fast_scores, fatigue_levels


    def simulate_driver_state(self):
        """
        Simulates driver state based on time spent looking away from the road.
        Returns a list of driver states: 'Responsive', 'Distracted', or 'Asleep'.
        """
        driver_states = []
        for _ in range(self.num_samples):
            time_looking_away = random.uniform(0, 10)  # Simulate time away from road (0 to 10 seconds)
            if time_looking_away > 6:
                driver_states.append("Asleep")
            elif 3 < time_looking_away <= 6:
                driver_states.append("Distracted")
            else:
                driver_states.append("Responsive")
        return driver_states


    def find_range_value(self, parameter=None, range_dict=None): 
        for (start,end), _ in range_dict.items(): 
            if start <= parameter <= end:
                return (start, end)

        return False
    

    def generate_timestamps(self):
        """
        Function to generate synthetic data for time stamps.
        """
        from datetime import datetime, timedelta

        time_interval = timedelta(seconds=3)
        start_time = datetime.now() 

        #Generate timstamps 
        timestamps = [start_time + i * time_interval for i in range(self.num_samples)]
        timestamps = [t.strftime('%Y-%m-%d %H:%M:%S') for t in timestamps]
        return timestamps