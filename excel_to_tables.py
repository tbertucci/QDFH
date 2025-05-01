import pandas as pd
import numpy as np

excel_file = pd.ExcelFile('QDFH.xlsx')

sheet_names = excel_file.sheet_names
data_sheets = sheet_names[1:-4]

singles = np.r_[0:31, 55:77, 93:len(data_sheets)]
singles = [data_sheets[i] for i in singles]


# single consonant treatments
single_treatment_tables = []

for sheet_name in singles: #[0:33]

        df = excel_file.parse(sheet_name) 
        print(f"Sheet: {sheet_name}")

        # get basic info
        number = df.iloc[1,1]
        treatment = df.iloc[2,1]
        environment = df.iloc[3, 1]
        
        table = df.iloc[5:17, :]
        
        # pivot table so rows = cols
        melted = table.melt(id_vars = 'A - Consonantism', var_name = 'Variable', value_name = 'Value')
        pivot = melted.pivot(index = 'Variable', columns = 'A - Consonantism', values = 'Value')
        pivot.set_index('Languages', inplace = True)
        pivot.reset_index(inplace = True)

        pivot = pivot.dropna(subset = ['Languages'])


        # deal with a/b/c versions
        pivot['version'] = pivot.groupby('Languages').cumcount().add(1)
        pivot['version'] = pivot['version'].apply(lambda x:  chr(97 + int(x)-1))

        pivot.insert(0, 'number', number)
        pivot.insert(0, 'treatment', treatment)
        pivot.insert(1, 'environment', environment)
        pivot.insert(2, 'position', 1)

        # clean language names and empty rows
        pivot['Languages'] = pivot['Languages'].str.replace('\n', ' ', regex = False)
        

        single_treatment_tables.append(pivot)


all_df = pd.concat(single_treatment_tables, axis = 0)



### two positions 
 
doubles = np.r_[31:47, 77:93]
doubles = [data_sheets[i] for i in doubles]


double_treatment_tables = []
n_consonants = 2

for sheet_name in doubles: 

        df = excel_file.parse(sheet_name) 
        print(f"Sheet: {sheet_name}")


        # get basic info
        number = df.iloc[1,1]
        treatment = df.iloc[2,1]
        environment = df.iloc[3, 1]

        treatment_tables = []
        
        for i in range(0, n_consonants): 
                if i == 0:
                        pos_table = df.iloc[5:17, :]
                elif i == 1:
                        pos_table = df.iloc[np.r_[5, 18:29], :]
                

                # pivot table so rows = cols
                melted =  pos_table.melt(id_vars = 'A - Consonantism', var_name = 'Variable', value_name = 'Value')
                pivot = melted.pivot(index = 'Variable', columns = 'A - Consonantism', values = 'Value')
                pivot.set_index('Languages', inplace = True)
                pivot.reset_index(inplace = True)

                pivot = pivot.dropna(subset = ['Languages'])

                # deal with a/b/c versions
                pivot['version'] = pivot.groupby('Languages').cumcount().add(1)
                pivot['version'] = pivot['version'].apply(lambda x:  chr(97 + int(x)-1))

                pivot.insert(0, 'number', number)
                pivot.insert(0, 'treatment', treatment)
                pivot.insert(1, 'environment', environment)
                pivot.insert(2, 'position', i+1)

                # clean language names and empty rows
                pivot['Languages'] = pivot['Languages'].str.replace('\n', ' ', regex = False)

                treatment_tables.append(pivot)
        
        double_treatment_table = pd.concat(treatment_tables, axis = 0)
        double_treatment_table.sort_values(['Languages'], inplace =True)
        double_treatment_tables.append(double_treatment_table)


double_treatment = pd.concat(double_treatment_tables, axis = 0)

 
# put all_df with double_treatments 
all_consonants_data = pd.concat([all_df, double_treatment], axis = 0)

all_consonants_data['Voice +/−'].value_counts()

all_consonants_data['voice'] = all_consonants_data['Voice +/−'].map({'+': 0,
                                                                      '−': 255,
                                                                      '+ (−)': 85,
                                                                      '− (+)': 170,
                                                                      '+/−': 127.5,
                                                                      '−/+': 127.5})


ipa_vals = pd.read_csv('IPA.csv')

place_dict = dict(zip(ipa_vals['IPA'], ipa_vals['Place\nvalue']))
place_dict['∅'] = 0
sonority_dict = dict(zip(ipa_vals['IPA'], ipa_vals['Sonority\nvalue']))
sonority_dict['∅'] = 0

all_consonants_data['place'] = all_consonants_data['IPA'].map(place_dict)
all_consonants_data['sonority'] = all_consonants_data['IPA'].map(sonority_dict)

all_consonants_data.dropna(subset = ['place', 'sonority'], inplace = True)

all_consonants_data.to_csv('all_consonants_data.csv')


#all_consonants_data = pd.read_csv('all_consonants_data.csv')

#all_consonants_data.columns

