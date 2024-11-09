#!/usr/bin/env python

import os
import typing
import sqlite3
import datetime

import pandas as pd
from icecream import ic

from graphreduce.node import GraphReduceNode, DynamicNode, SQLNode
from graphreduce.graph_reduce import GraphReduce
from graphreduce.enum import ComputeLayerEnum, PeriodUnit, StorageFormatEnum, ProviderEnum, SQLOpType
from graphreduce.models import sqlop


data_path = '/'.join(os.path.abspath(__file__).split('/')[0:-1]) + '/data/cust_data'
print(data_path)



def test_custom_node_definition():
    class CustNode(GraphReduceNode):
        def do_filters(self):
            pass
        def do_annotate(self):
            pass
        def do_normalize(self):
            pass
        def do_reduce(self, reduce_key):
            pass
        def do_labels(self, reduce_key):
            pass
        def do_post_join_annotate(self):
            pass
    cust = CustNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt = 'csv',
            prefix='cust',
            compute_layer=ComputeLayerEnum.pandas,
            date_key=None
            )
    assert isinstance(cust, CustNode)


def test_custom_node_graph():
    class CustNode(GraphReduceNode):
        def do_filters(self):
            pass
        def do_annotate(self):
            pass
        def do_normalize(self):
            pass
        def do_reduce(self, reduce_key):
            pass
        def do_labels(self, reduce_key):
            pass
        def do_post_join_annotate(self):
            pass
    cust = CustNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt = 'csv',
            prefix='cust',
            compute_layer=ComputeLayerEnum.pandas,
            date_key=None
            )
    class OrderNode(GraphReduceNode):
        def do_filters(self):
            pass
        def do_annotate(self):
            pass
        def do_normalize(self):
            pass
        def do_reduce(self, reduce_key):
            return self.prep_for_features().groupby(self.colabbr(reduce_key)).agg(**{
                self.colabbr("num_orders"): pd.NamedAgg(column=self.colabbr(self.pk), aggfunc="count")
                }).reset_index()
        def do_labels(self, reduce_key):
            pass
        def do_post_join_annotate(self):
            pass
    order = OrderNode(
            fpath=os.path.join(data_path, 'orders.csv'),
            pk='id',
            fmt = 'csv',
            prefix='ord',
            compute_layer=ComputeLayerEnum.pandas,
            date_key='ts'
            )
    gr = GraphReduce(
            name='test_two_node_graph',
            parent_node=cust,
            compute_layer=ComputeLayerEnum.pandas
            )
    gr.add_entity_edge(
            parent_node=cust,
            relation_node=order,
            parent_key='id',
            relation_key='customer_id',
            relation_type='parent_child',
            reduce=True
            )
    gr.do_transformations()
    ic(gr.parent_node.df.head())
    assert len(gr.parent_node.df) == 4

   


def test_dynamic_node_instance():
    node = DynamicNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt='csv',
            prefix='cust',
            compute_layer=ComputeLayerEnum.pandas,
            date_key=None
            )
    assert isinstance(node, DynamicNode)


def test_get_data():
    node = DynamicNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt='csv',
            prefix='cust',
            compute_layer=ComputeLayerEnum.pandas,
            date_key=None
            )
    node.do_data()
    print(node.df)
    assert len(node.df) == 4


def test_filter_data():
    node = DynamicNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt='csv',
            prefix='cust',
            compute_layer=ComputeLayerEnum.pandas,
            date_key=None
            )
    node.do_data()
    node.do_filters()
    print(node.df)
    assert len(node.df) == 4


def test_multi_node():

    cust_node = DynamicNode(
            fpath=os.path.join(data_path, 'cust.csv'),
            fmt='csv',
            prefix='cust',
            date_key=None,
            pk='id',
            )

    order_node = DynamicNode(
            fpath=os.path.join(data_path, 'orders.csv'),
            fmt='csv',
            prefix='ord',
            date_key='ts',
            pk='id',
            )

    gr = GraphReduce(
            parent_node=cust_node,
            fmt='csv',
            compute_layer=ComputeLayerEnum.pandas,
            auto_features=True,
            compute_period_val=730
            )
    gr.add_node(cust_node)
    gr.add_node(order_node)

    assert len(gr) == 2

    gr.add_entity_edge(
            parent_node=cust_node,
            relation_node=order_node,
            parent_key='id',
            relation_key='customer_id',
            relation_type='parent_child',
            reduce=True
            )

    gr.do_transformations()
    print(gr.parent_node.df)
    assert len(gr.parent_node.df) == 4



def _setup_sqlite():
    dbfile = os.path.join(data_path, 'cust.db')
    conn = sqlite3.connect(dbfile)
    files = [x for x in os.listdir(data_path) if x.endswith('.csv')]
    for f in files:
        df = pd.read_csv(f"{data_path}/{f}")
        name = f.split('.')[0]
        df.to_sql(name, conn, if_exists='replace', index=False)
    return conn

def _teardown_sqlite(conn):
    try:
        dbfile = os.path.join(data_path, 'cust.db')
        conn.close()
        os.system(f"rm {dbfile}")
    except Exception as e:
        ic(e)


class CustNode(SQLNode):
    def do_annotate(self) -> typing.Union[sqlop, typing.List[sqlop]]:
        return [
            sqlop(optype=SQLOpType.select, opval=f"*, LENGTH({self.colabbr('name')}) as {self.colabbr('name_length')}")
        ]
    
    def do_filters(self) -> typing.Union[sqlop, typing.List[sqlop]]:
        return [
            sqlop(optype=SQLOpType.where, opval=f"{self.colabbr('id')} < 3")
        ]
    
    def do_normalize(self):
        pass
    
    
    def do_reduce(self, reduce_key):
        pass
    
    def do_post_join_annotate(self):
        pass
    
    def do_post_join_filters(self):
        pass


class NotificationNode(SQLNode):
    def do_annotate(self) -> typing.List[sqlop]:
        return [
            sqlop(optype=SQLOpType.select, opval=f"*, strftime('%m', {self.colabbr('ts')})")
        ]

    def do_filters(self) -> typing.List[sqlop]:
        return [
            sqlop(optype=SQLOpType.where, opval=f"{self.colabbr('ts')} > '2022-06-01'")
        ]

    def do_normalize(self):
        pass

    def do_reduce(self, reduce_key):
        return [
            # Shouldn't this just be a select?
            sqlop(optype=SQLOpType.aggfunc, opval=f"count(*) as {self.colabbr('num_notifications')}"),
            sqlop(optype=SQLOpType.agg, opval=f"{self.colabbr(reduce_key)}"),
        ]




def test_sql_node_definition():
    conn = _setup_sqlite()
    cust = CustNode(fpath='cust',
                prefix='cust',
                client=conn,
                compute_layer=ComputeLayerEnum.sqlite,
                columns=['id','name'])
    notif = NotificationNode(fpath='notifications',
                prefix='not',
                client=conn,
                compute_layer=ComputeLayerEnum.sqlite,
                columns=['id', 'customer_id', 'ts'],
                date_key='ts'
        )
    _teardown_sqlite(conn)
    assert isinstance(cust, CustNode)



def test_sql_graph_transform():
    conn = _setup_sqlite()
    cust = CustNode(fpath='cust',
                prefix='cust',
                client=conn,
                compute_layer=ComputeLayerEnum.sqlite,
                columns=['id','name'])
    notif = NotificationNode(fpath='notifications',
                prefix='not',
                client=conn,
                compute_layer=ComputeLayerEnum.sqlite,
                columns=['id', 'customer_id', 'ts'],
                date_key='ts'
        )
    gr = GraphReduce(
            name='sql_dialect_example',
            parent_node=cust,
            compute_layer=ComputeLayerEnum.sqlite,
            use_temp_tables=True,
            lazy_execution=False
            )
    gr.add_node(cust)
    gr.add_node(notif)
    gr.add_entity_edge(cust, notif, parent_key='id', relation_key='customer_id', reduce=True)
    gr.do_transformations_sql()
    _teardown_sqlite(conn)
    assert len(gr) == 2



def test_sql_graph_auto_fe():
    conn = _setup_sqlite()
    cust = SQLNode(fpath='cust',
                pk='id',
                prefix='cust',
                client=conn,
                compute_layer=ComputeLayerEnum.sqlite,
                columns=['id','name'])

    notif = SQLNode(fpath='notifications',
                    prefix='not',
                    pk='id',
                    client=conn,
                    compute_layer=ComputeLayerEnum.sqlite,
                    columns=['id','customer_id','ts'],
                    date_key='ts')

    ni = SQLNode(fpath='notification_interactions',
                    prefix='ni',
                    pk='id',
                    client=conn,
                    compute_layer=ComputeLayerEnum.sqlite,
                    columns=['id','notification_id','interaction_type_id','ts'],
                    date_key='ts')

    order = SQLNode(fpath='orders',
                   pk='id',
                   prefix='ord',
                   client=conn,
                   compute_layer=ComputeLayerEnum.sqlite,
                   columns=['id','customer_id','ts','amount'],
                    date_key='ts')

    gr = GraphReduce(
        name='sql_autofe',
        parent_node=cust,
        # Cut date for filtering.
        cut_date=datetime.datetime(2023, 6, 30),
        # Feature parameters.
        compute_period_unit=PeriodUnit.day,
        compute_period_val=730,
        # Label parameters.
        label_node=order,
        label_field='amount',
        label_operation='sum',
        label_period_unit=PeriodUnit.day,
        label_period_val=30,
        compute_layer=ComputeLayerEnum.sqlite,
        use_temp_tables=True,
        lazy_execution=False,
        # Auto feature engineering params.
        auto_features=True,
        auto_feature_hops_back=3,
        auto_feature_hops_front=1
    )
    gr.add_node(cust)
    gr.add_node(order)
    gr.add_node(notif)
    gr.add_node(ni)

    gr.add_entity_edge(
        cust,
        notif,
        parent_key='id',
        relation_key='customer_id',
        reduce=True
    )

    gr.add_entity_edge(
        notif,
        ni,
        parent_key='id',
        relation_key='notification_id',
        reduce=True
    )

    gr.add_entity_edge(
        cust,
        order,
        parent_key='id',
        relation_key='customer_id',
        reduce=True
    )
    gr.plot_graph('cust_graph.html')
    gr.do_transformations_sql()
    d = pd.read_sql_query(f"select * from {gr.parent_node._cur_data_ref}", conn)
    ic(d)
    _teardown_sqlite(conn)
    assert len(d) == 4


