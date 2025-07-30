# neo4j_connector.py
from neo4j import GraphDatabase


class Neo4j:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def sync_query(self, cypher, params=None):
        """同步执行Cypher查询"""
        with self._driver.session() as session:
            try:
                # 使用事务处理
                with session.begin_transaction() as tx:
                    result = tx.run(cypher, parameters=params)
                    # 在事务关闭前处理结果
                    records = list(result)
                    tx.commit()
                    return records
            except Exception as e:
                print(f"Neo4j查询错误: {str(e)}")
                return []
                
    async def query(self, cypher, params=None):
        """异步版本的query方法，用于支持异步调用"""
        # 由于neo4j-python-driver暂不直接支持异步API，这里使用同步方法
        return self.sync_query(cypher, params)

    def __del__(self):
        self._driver.close()