import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import aiomysql


async def get_any_entities_contain_name(conn_params, name_part: str) -> Optional[dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Use the LIKE operator with wildcard characters to search for any occurrence of name_part
                await cur.execute("SELECT id,name,type FROM entities WHERE MATCH(name) AGAINST (%s) ", (name_part,))
                return await cur.fetchall()


async def add_entity(conn_params, entity_name: str, entity_type: str):
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Make sure to include both name and type in the VALUES
                await cur.execute("INSERT INTO entities (name, type) VALUES (%s, %s);", (entity_name, entity_type))
                # Commit the transaction
                await conn.commit()
                # Fetch the ID of the last inserted row
                entity_id = cur.lastrowid
                return entity_id
            
            
async def check_and_add_news_entity(conn_params, news_id: int, entity_id: int):
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # First, check if the news_entity combination already exists
                await cur.execute("SELECT 1 FROM newsEntities WHERE news_id = %s AND entity_id = %s;", (news_id, entity_id))
                result = await cur.fetchone()
                
                if result is None:
                    # The news_entity combination does not exist, so insert it
                    await cur.execute("INSERT INTO newsEntities (news_id, entity_id) VALUES (%s, %s);", (news_id, entity_id))
                    await conn.commit()
                    return True, cur.lastrowid  # Return True to indicate a new record was added, along with the new row ID
                    
                else:
                    # The news_entity combination already exists
                    return False, None