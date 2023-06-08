import pandas as pd
from pecista import MLInterface, Postgres
from requests import get
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from itertools import repeat
from time import sleep
pd.options.display.memory_usage

PATH_DATA = '../data'
PATH_OUT = '../out'

def check_compatibilidades(
        mlb:str,
        access_token:str) -> get:
    """_summary_

    Args:
        mlb (str): item_id MercadoLivre (MLB)
        access_token (str): Token de acesso API MercadoLivre

    Returns:
        get: Resposta da requisicao em JSON
    """    

    url = f"https://api.mercadolibre.com/items/{mlb}/compatibilities"
    headers = {
        "Authorization": f"Bearer {access_token}"
        }
    response =get(url, headers=headers)

    return response.json(), response.status_code

def interaction(
        item_id:str,
        token:str) -> dict:

    try:
        compatibilities, response_status_code = check_compatibilidades(item_id, token)
        
        while (compatibilities == 429) or (compatibilities == 500):
            sleep(0.5)
            compatibilities, response_status_code = check_compatibilidades(item_id, token)

        qtd_comp = len(compatibilities['products'])

        if qtd_comp > 0:
            return {'item_id':item_id, 'compatibilitie': str(True), 'qtd_compatibilities': int(qtd_comp), 'result_response_status_code': int(response_status_code)}
        else:
            return {'item_id':item_id, 'compatibilitie': str(False), 'qtd_compatibilities': int(qtd_comp), 'result_response_status_code': int(response_status_code)}

    except KeyError as erro:
        if erro == 'catalog_compatibilities_count':
            return {'item_id':item_id, 'compatibilitie': 'Esse MLB nao entra compatibilidades', 'qtd_compatibilities': int(qtd_comp), 'result_response_status_code': int(response_status_code)}


if __name__ == '__main__':

    ML = MLInterface(1)
    ACCESS_TOKEN = ML._get_token(1)

    with Postgres() as db: df_item_ids = db.query('SELECT item_id FROM "ECOMM".ml1_info')
    df_aux = pd.DataFrame(columns=['item_id', 'compatibilitie', 'qtd_compatibilities', 'result_response_status_code'])

    print(f'Quantidades de IDs a serem verificados: {df_item_ids.item_id.count()}\n')
    with ThreadPoolExecutor() as task:
        for future in tqdm(task.map(interaction, df_item_ids.item_id, repeat(ACCESS_TOKEN)), total=len(df_item_ids)):
            df_aux.loc[len(df_aux)] = future

    df_aux.to_csv(f'{PATH_OUT}/resultado.csv', index=False)
