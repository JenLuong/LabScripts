# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 14:28:45 2025

@author: Jen Luong
"""

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# Constants
FINALCONC_UM = 2
FINALVOL_UL = 300
MAX_TIP_VOL_UL = 50
BLANK_CONTROL_WELLS = {"F5", "A12"}
GFP_WELLS = {"A1", "F9"}


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    #Ask user to find Protein Concentration Files
    file_path = filedialog.askopenfilename(
        title="Select Protein Concentration .CSV File",
        filetypes=[("CSV files", "*.csv")]
    )
    #If there is no file then an error message will appear
    if not file_path:
        messagebox.showerror("Error", "No file selected.")
        return
    #Double check that the file path is valid, if not an error message will appear
    try:
        enzfile = pd.read_csv(file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file:\n{e}")
        return
    #Checks for the columns labeled 'Well_ID' and 'Conc_uM_Final'
    if 'Well_ID' not in enzfile.columns or 'Conc_uM_Final' not in enzfile.columns:
        messagebox.showerror("Error", "CSV must contain 'Well_ID' and 'Conc_uM_Final'.")
        return
    #Remove the leading 0 from well id. I.E. changes A01 to A1
    enzfile['Well_ID'] = enzfile['Well_ID'].str.replace(r'([A-H])0?(\d)', r'\1\2', regex=True)
    #Creates a dictionary associating well ID to the concentration
    enzlist = enzfile['Well_ID'].tolist()
    conclist = enzfile['Conc_uM_Final'].tolist()
    enzconclist = dict(zip(enzlist, conclist))
    #Create dataframe containing the volumes to add of protein and buffer to create a plate with the desired final concentration
    dataframe = create_dataframe(enzconclist, conclist)

    # Ask user for output file name
    unitrun = simple_input("Enter run number (e.g. R1_1):")
    if not unitrun:
        messagebox.showwarning("Cancelled", "Operation cancelled.")
        return

    #Create your file. If the file name already exists, prompt to ask for overwrite
    runmapfile = f"Protein_Norm_{unitrun}_{FINALCONC_UM}uM.csv"
    if os.path.exists(runmapfile):
        overwrite = messagebox.askyesno("File Exists", f"{runmapfile} already exists.\nOverwrite?")
        if not overwrite:
            return
    #Create your csv file with the dataframe and show message it ws successful. If csv was not create, an error will appear
    try:
        dataframe.to_csv(runmapfile, index=False)
        messagebox.showinfo("Success", f"File saved as:\n{runmapfile}")
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save file:\n{e}")

#Function to create your dataframe
def create_dataframe(enzconclist, conclist):
    #create data_rows list
    data_rows = []
    #loop over every location in your dictionary
    for loc, conc in enzconclist.items():
        #set all location names to uppercase
        loc = loc.upper()
        #set all concentrations to floats
        conc = float(conc)
        #check blank control wells for any blanks
        if loc in BLANK_CONTROL_WELLS:
            #take the average of all concentrations in the file to figure out how much blank material to add
            average = sum(enzconclist.values()) / len(enzconclist)
            protvoladd = (FINALCONC_UM * FINALVOL_UL) / average #M1V1 = M2V2
            protvoladd = min(protvoladd, MAX_TIP_VOL_UL)
            buffvoladd = FINALVOL_UL - protvoladd
            dividecounter = 1
        #Set both buffer volume and protein volume to 0 if there is a 0 concentration of if it is a GFP well
        elif conc == 0 or loc in GFP_WELLS:
            protvoladd = 0
            buffvoladd = 0
            dividecounter = 1
        #For all other wells, calculate how much protein and dilution buffer to add to make the desired final concentration
        else:
            dividecounter = 1
            orig_protvoladd = (FINALCONC_UM * FINALVOL_UL) / conc #M1V1 = M2V2
            protvoladd = orig_protvoladd
            buffvoladd = FINALVOL_UL - protvoladd
            #If the protein vol add exceeds the tip volume, divide until the volume is under the mas tip volume
            while protvoladd > MAX_TIP_VOL_UL:
                dividecounter += 1
                protvoladd = orig_protvoladd / dividecounter
                buffvoladd = (FINALVOL_UL - orig_protvoladd) / dividecounter
        #append a list containing your source well, destination well, dilution buffer volume, protein buffer volume, and the number of times you divided into the next index of your 'data_rows' list
        data_rows.append([loc, loc, protvoladd, buffvoladd, dividecounter])
    #create a dataframe of your data_rows list with column headers as your index ids
    df = pd.DataFrame(data_rows, columns=['SourceWell', 'DestWell', 'PPVol', 'DilVol', 'DivideCounter'])
    #add replicates of the line in the dataframe by the number of times divided. I.E if the line is [A1, A1, 30, 120, 2] (DvidieCounter = 2); create an additional line in your data base with the same values so that there are 2 identical lines
    df = df.loc[df.index.repeat(df['DivideCounter'])].reset_index(drop=True)
    return df

#function for a user input prompt for naming
def simple_input(prompt):
    import tkinter.simpledialog as sd
    return sd.askstring("Input Required", prompt)


if __name__ == '__main__':
    main()