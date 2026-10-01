import sqlite3
import re
from pathlib import Path


# ==========================
# CONFIG
# ==========================

BASE_DIR = Path(__file__).parent


INPUT_DB = BASE_DIR / "minecraft.db"

OUTPUT_DB = BASE_DIR / "minecraft_clean.db"



# ==========================
# NORMALIZER
# ==========================

def normalize_name(text):

    """
    Convert:

    Nether Brick Slab

    into:

    netherbrickslab
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]",
        "",
        text
    )

    return text



# ==========================
# FILTER
# ==========================

IGNORE_WORDS = [

    "_inventory",

    "_pressed",

    "_top",

    "_bottom",

    "_left",

    "_right",

    "_open",

    "_closed",

    "_side",

    "_particle",

    "_stage"

]



def should_keep(name):

    name = name.lower()

    for word in IGNORE_WORDS:

        if word in name:

            return False

    return True



# ==========================
# CREATE DB
# ==========================

def create_database():

    if OUTPUT_DB.exists():

        OUTPUT_DB.unlink()


    conn = sqlite3.connect(
        OUTPUT_DB
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE minecraft_names (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            minecraft_id TEXT UNIQUE,

            display_name TEXT,

            normalized_name TEXT UNIQUE,

            type TEXT

        )
        """
    )


    cursor.execute(
        """
        CREATE INDEX idx_normalized
        ON minecraft_names(normalized_name)
        """
    )


    conn.commit()

    return conn



# ==========================
# CLEAN + INSERT
# ==========================

def build_database():

    source = sqlite3.connect(
        INPUT_DB
    )


    source_cursor = source.cursor()


    target = create_database()


    target_cursor = target.cursor()


    source_cursor.execute(
        """
        SELECT
            minecraft_id,
            display_name,
            type

        FROM minecraft_names
        """
    )


    kept = 0

    removed = 0



    for minecraft_id, display_name, item_type in source_cursor.fetchall():


        if not should_keep(minecraft_id):

            removed += 1

            continue



        normalized = normalize_name(
            display_name
        )


        try:

            target_cursor.execute(
                """
                INSERT INTO minecraft_names
                (
                    minecraft_id,
                    display_name,
                    normalized_name,
                    type
                )

                VALUES (?, ?, ?, ?)

                """,
                (
                    minecraft_id,
                    display_name,
                    normalized,
                    item_type
                )
            )


            kept += 1


        except sqlite3.IntegrityError:

            removed += 1



    target.commit()


    source.close()

    target.close()


    print(
        "======================"
    )

    print(
        "Final database built"
    )

    print(
        f"Kept    : {kept}"
    )

    print(
        f"Removed : {removed}"
    )

    print(
        "======================"
    )



# ==========================
# TEST
# ==========================

def test():

    conn = sqlite3.connect(
        OUTPUT_DB
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            display_name,
            normalized_name

        FROM minecraft_names

        WHERE display_name LIKE '%Nether%'

        LIMIT 10
        """
    )


    print(
        "\nTest:\n"
    )


    for row in cursor.fetchall():

        print(
            row[0],
            "=>",
            row[1]
        )


    conn.close()



if __name__ == "__main__":

    build_database()

    test()

    print(
        "\nCreated:",
        OUTPUT_DB
    )