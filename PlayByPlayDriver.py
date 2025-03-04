import sys, os, time, re
import pandas as pd
import pyodbc

from OnCourtDriver import get_file_paths, clean_player_name
from parsers.PlayParser import parse_entry
from progress_bar.ProgressBar import update_progress

def main():
    """
    The entry point for the play-by-play data parser. This function is responsible 
    for verifying the input arguments, in addition to opening the files, calling the
    play-by-play parser, then running the secondary parser on the points data.

    Usage:

    python PlayByPlayDriver.py [input_file/input_path] [output_path]
    """
    try: 
        if (len(sys.argv) != 3):
            raise SyntaxError("Invalid input arguments. Input command should be \
                python PlayByPlayDriver.py [input_file/input_path] [output_path]\
                ")
        if (not os.path.exists(sys.argv[1])):
            raise FileNotFoundError(sys.argv[1] + " does not exist")
        if (os.path.exists(sys.argv[2])):
            raise FileExistsError(sys.argv[2] + " already exists")
        
        run(sys.argv[1], sys.argv[2])

    except SyntaxError as e:
        print(e)
    except FileNotFoundError as e:
        print(e)
    except FileExistsError as e:
        print(e)

def run(input_path: str, output_path: str):
    """
    This function is responsible for finding all the files specified by 'input_path',
    parsing the contents of the file, calling the PlayParser, then processing that
    into a usable format.

    Preconditions:
    --------------
    Note that this function assumes that input_path already exists and that 
    output_path does not exist.

    Parameters:
    -----------
    input_path:  The input path denoting the file (or folder containing the 
                 files) we want to parse. Note that this can be a single file or
                 a folder containing .xlsl files.
    output_path: The output path where we plan on storing the collected data.
    """
    files = get_file_paths(input_path)
    # Output - an array of Pandas.DataFrames
    output = []
    i = 1
    for file_path in files:
        print("Parsing " + file_path + " (" + str(i) + "/" + str(len(files)) + ")")
        file_contents = open_file(file_path)
        output.append(get_play_data(file_contents))
    
    os.mkdir(output_path)
    for data in output:
        data.to_excel(output_path +"/out.xlsx", index=False)

def open_file(path: str) -> pd.DataFrame:
    """
    This file is responsible for obtaining the contents of the .xlsx specified 
    by path.

    Parameters:
    -----------
    path: A file path to the .xlsx file we want to parse.

    Return Value: 
    -------------
    This function returns a Pandas.DataFrame containing the contents of the .xlsx
    file we are opening.
    """
    df = pd.read_excel(path, engine='openpyxl', index_col=None, header=None)
    df = df.iloc[1:]
    return df

def get_play_data(df: pd.DataFrame):
    """
    Not exactly sure how this function should work, but the general idea is it
    should:
        1. Obtain the play-by-play data (in addition to other meta data needed 
           from df)
        2. Parse the play-by-play data to write the "usable" data
    
    Parameters:
    -----------
    df: The Pandas.DataFrame containing match info.

    Returns:
    --------
    A Pandas.DataFrame containing usable data obtained from the play parser.
    """
    frames = []
    for i, row in df.iterrows():
        # Run PlayParser
        # Call function to parse output of PlayParser
        # Add function output to output DataFrame
        p1_name = clean_player_name(row[0])
        p2_name = clean_player_name(row[1])
        date = str(row[3])[0:10]
        entry_key = p1_name + " " + p2_name + " " + date

        if (isinstance(row[15], str) and not re.match("\s+", row[15])):
            df_play = parse_entry(row[15])
            frames.append(parse_play_dataframe(df_play, entry_key))
        update_progress(i / len(df.index))

    return pd.concat(frames)

def parse_play_dataframe(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    This function is responsible for calculating the following entries using the 
    output from parse_enty in PlayParser.py:
        1. Set number
        2. P1 games won
        3. P2 games won
        4. Set winner
        5. Game number
        6. Game winner
        7. Point number
        8. Point winner
        9. Point server.
    
    Once this data is calculated, it will be output to the user in the form of a
    Pandas.Dataframe.

    Parameters:
    -----------
    df: The Pandas.DataFrame we want to analyze.
    key: The key corresponding to the particular match that it being played.

    Returns:
    --------
    A Pandas.DataFrame containing the above information.
    """ 
    output_columns = ["Key", "SetNo", "P1GamesWon", "P2GamesWon", "SetWinner", 
        "GameNo", "GameWinner", "PointNumber", "PointWinner", "PointServer", "Score"]
    output_df = pd.DataFrame(columns=output_columns)
    output_df = output_df.iloc[1:]

    set_no = 1
    game_no = 0
    point_no = 0
    point_server = 0

    for i, row in df.iterrows():
        set_games = row[1].split("-")
        if (len(set_games) == 2):
            set_winner = 1 if set_games[0] > set_games[1] else 2
            if (row[0] == "EndGame"):
                output_df = output_df.append({
                    "Key": key,
                    "SetNo": set_no,
                    "P1GamesWon": set_games[0],
                    "P2GamesWon": set_games[1],
                    "SetWinner": 0,
                    "GameNo": game_no,
                    "GameWinner": set_winner,
                    "PointNumber": point_no, 
                    "PointWinner": set_winner,
                    "PointServer": point_server,
                    "Score": row[0],
                }, ignore_index=True)
                game_no += 1
            elif (row[0] == "EndSet" ):
                output_df = output_df.append({
                    "Key": key,
                    "SetNo": set_no,
                    "P1GamesWon": set_games[0],
                    "P2GamesWon": set_games[1],
                    "SetWinner": set_winner,
                    "GameNo": game_no,
                    "GameWinner": set_winner,
                    "PointNumber": point_no, 
                    "PointWinner": set_winner,
                    "PointServer": point_server,
                    "Score": row[0]
                }, ignore_index=True)
                game_no = 0
                set_no += 1
            elif (row[0] == "End"):
                pass
            else:
                remove_brackets = row[0].replace("[", "").replace("]", "")
                point_server = 2
                remove_asterisk = remove_brackets.replace("*", "")
                games = remove_asterisk.split("-")

                try:
                    if (remove_brackets.index('*') == 0): point_server = 1
                except ValueError:
                    point_server = -1

                output_df = output_df.append({
                    "Key": key,
                    "SetNo": set_no,
                    "P1GamesWon": set_games[0],
                    "P2GamesWon": set_games[1],
                    "SetWinner": 0,
                    "GameNo": game_no,
                    "GameWinner": 0,
                    "PointNumber": point_no, 
                    "PointWinner": 1 if games[0] > games[1] else 2,
                    "PointServer": point_server,
                    "Score": row[0],
                }, ignore_index=True)
            point_no += 1
    return output_df

def connectToSQLDatabase():
    """
    This function is to connect to the Azure SQL database for the project. It only needs to be called once.
    There is no input and the output is of type "conn". It is used for executing SQL functions in the database.
    """
    server = 'tennismodelling.database.windows.net'
    database = 'TennisModelling'
    username = 'tennisAdmin'
    password = '{tennis2022!}'   
    driver= '{ODBC Driver 17 for SQL Server}'
    return pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

if __name__ == "__main__":
    start = time.time()
    main()
    print("Elapsed time: " + str(time.time() - start))