import uuid

import pandas as pd

from src.models import ItemCreateIventory


def transform_file_into_request_objects(df: pd.DataFrame, shop_id: uuid.UUID) -> list[ItemCreateIventory]:
    """
    Transform an excel file into a list of ItemCreateIventory objects.
    :param df: dataframe to transform
    :param shop_id: shop id on which behalf the transformation is done
    :return: a list of ItemCreateIventory items
    """
    if "name" not in df.columns or\
            "description" not in df.columns or\
    "photo_url" not in df.columns or\
    "price" not in df.columns or\
    "percent_point_allocation" not in df.columns:
        raise ValueError("Badly formed excel file")
    df_needed = df[["name", "description", "photo_url", "price", "percent_point_allocation"]]
    df_needed.fillna("", inplace=True)
    items = [None] * len(df_needed)
    # iterate throw rows, so use numpy, as dataframe is columnar format
    for idx, row in enumerate(df_needed.to_numpy()):
        items[idx] = ItemCreateIventory(name=row[0], description=row[1], photo_url=row[2],
                                        price=row[3], percent_point_allocation=row[4],
                                        shop_id=shop_id)
    return items
