# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 14:26:58 2020

@author: WeiKangLiang
"""
import numpy as np
import pandas as pd
import datetime
import itertools
import random
import copy

'''
在所有儲格塞入商品資訊
'''
def Warehouse_items(Warehouse_dict,x,y,z,position,product_id,name,amount,unit):
    #global Warehouse_dict ????
    '''
    整理每個商品的儲格位置資訊
    '''
    #position = ",".join([str(x),str(y),str(z),str(position)])
    position = (x,y,z,position)
    Warehouse_dict[position] = {"product_id":str(product_id),"name":str(name),"amount":amount,"unit":str(unit)}
    return Warehouse_dict

'''
整理每個商品存在的走道與數量資訊
'''
def items_positions(Warehouse_dict, items_position_dict, Warehouse_container_interval,first_container_x):
    '''
    整理每個商品存在的走道與數量資訊
    robot_arm_number: check the product is under the control of which robot arm, ranged from 0 ~ N 
    '''
    for item_position in Warehouse_dict:
        item_info = Warehouse_dict.get(item_position)
        if item_info["product_id"] != None:
            product_id = item_info.get("product_id")
            name = item_info.get("name")
            amount = item_info.get("amount")
            position = item_position
            robot_arm_number = int((position[0]-first_container_x)/Warehouse_container_interval)
            if product_id in items_position_dict:
                items_position_dict[product_id].get('robot_arm_number').append(robot_arm_number)
                items_position_dict[product_id].get('name').append(name)
                items_position_dict[product_id].get('amount').append(amount)
                items_position_dict[product_id].get('position').append(position)
            else:
                items_position_dict[product_id] = {"robot_arm_number":[robot_arm_number], "name":[name],"amount":[amount],"position":[position]}            
        else:
            pass
        

    return items_position_dict
# =============================================================================
#     position = (x,y,z) 
#     robot_arm_number = int((x-first_container_x)/Warehouse_container_interval)+1
#     if item_id in items_position_dict:
#         items_position_dict[item_id].get('robot_arm_number').append(robot_arm_number)
#         items_position_dict[item_id].get('amount').append(amount)
#         items_position_dict[item_id].get('position').append(position)
#     else:
#         items_position_dict[item_id] = {"robot_arm_number":[robot_arm_number],"amount":[amount],"position":[position]}
#     return items_position_dict
# =============================================================================

'''
整理每個商品存在的走道與數量資訊舊版本
'''
def items_positions_old(items_position_dict,item_id,x,y,z,amount,Warehouse_container_interval,first_container_x):
    '''
    整理每個商品存在的走道與數量資訊
    check the product is under the control of which robot arm
    '''
    position = (x,y,z) 
    robot_arm_number = int((x-first_container_x)/Warehouse_container_interval)
    if item_id in items_position_dict:
        items_position_dict[item_id].get('robot_arm_number').append(robot_arm_number)
        items_position_dict[item_id].get('amount').append(amount)
        items_position_dict[item_id].get('position').append(position)
    else:
        items_position_dict[item_id] = {"robot_arm_number":[robot_arm_number],"amount":[amount],"position":[position]}
    return items_position_dict

'''
根據很多因素考慮每個機械手臂所要先撿的商品順序
'''
def News_Feed_func(exist_time,critical_exist_time,order_similarity,order_priority,path_length,longest_path,item_layer,highest_layer):
    '''
    決定先撿的商品順序
    references:
        https://thefederalist.com/2014/02/20/we-cracked-the-code-on-how-the-facebook-news-feed-algorithm-works/
    假設商品位置都會在每個走道的差不多位置
    every factor max: 10
    exist_time: 待處理訂單商品存在時間
    critical_exist_time: 希望待處理訂單商品不要超過這個時間還未處理，超過這個時間優先度上升
    order_similarity: 訂單商品內相似度，相似度高就優先處理
    path_length: 平面圖上，商品距離出口位置
    item_layer: 商品樓層數
    path_score: 位置離出口比較近，優先度上升
    
    order_score: 訂單順序，先放著再考慮要不要加入
    News_feed_score = time_score * order_similarity * path_score * order_score
    '''
    time_score = critical_exist_time**(exist_time/critical_exist_time)
    path_score = ((1.01-path_length/longest_path)*(1.01-item_layer/highest_layer))
    News_feed_score = time_score * order_similarity * path_score
    return News_feed_score

'''Ethan'''
'''robot arm time'''
def cal_robot_time(robot_arm_info,robot_arm_missions):
    
    total_robot_arm_num = len(robot_arm_info.get('robot_arm_number'))
    robot_remain_time = [0]*total_robot_arm_num
    current_time = datetime.datetime.now()
    for i in range(total_robot_arm_num):
        temp_robot_arm_info = robot_arm_missions.get(str(i))
        missions = temp_robot_arm_info.get('mission_list')
        executed_time_for_first_mission = (current_time - temp_robot_arm_info.get('mission_start_time')).total_seconds()

        for missionnum in range(len(missions)):
            if missionnum != 1:
                robot_remain_time[i] += missions[missionnum].get('mission_consume_time')
            else:
                remain_time_for_first_mission = missions[missionnum].get('mission_consume_time') - executed_time_for_first_mission
                robot_remain_time[i] += remain_time_for_first_mission
    
    return robot_remain_time

'''計算貨品提取可能組合'''    
def cal_products_cotent_combination(items_position_dict,order):
    
    all_product_combination = []
    products = order.get('content')
    for product in products:
        temp_product_combination = []
        product_id = product.get("product_id")
        order_amount = product.get("amount")
        order_position = items_position_dict[product_id].get('position')
        
        for i in range(len(order_position)):
            order_position[i] = order_position[i][0:3] #just need xyz coordinate the fourth position is same location but different content
        item_amount_info = items_position_dict[product_id].get('amount')
        '''計算組合'''
        for num in range(1,len(item_amount_info)+1):
            less_order_amount = 0
            amount_subsets = list(itertools.combinations(item_amount_info, num))
            index_amount = list(itertools.combinations(enumerate(item_amount_info), num))
            '''提取位置排列組合'''
            for index_num in range(len(index_amount)):
                temp_index_amount = index_amount[index_num]
                temp_amount_subsets_index = []
                subset = amount_subsets[index_num]
                total_amount = sum(subset)
                if total_amount >= order_amount:
                    for index_num_num in range(len(temp_index_amount)):
                        temp_amount_subsets_index.append(order_position[temp_index_amount[index_num_num][0]])
                    temp_product_combination.append(temp_amount_subsets_index)
                else:
                    less_order_amount += 1
            
            '''if sum of all combinations is bigger than order_amount, then it doesn't need to add more position'''
            if less_order_amount == 0:
                break
            
        all_product_combination.append(temp_product_combination)
        
    return all_product_combination

'''計算訂單撿貨最佳解'''
def cal_order_pic_seq(all_product_combination,robot_remain_time,Warehouse_container_interval,first_container_x):
    
    all_product_get_procedure = list(itertools.product(*all_product_combination))
    all_robot_remain_time = [[]]*len(all_product_get_procedure)
    for procedure_num in range(len(all_product_get_procedure)):
        product_get_procedure = all_product_get_procedure[procedure_num]
        merged_product_get_procedure = []
        for first_layer in product_get_procedure:
            for second_layer in first_layer:
                merged_product_get_procedure.append(second_layer)
        
        temp_robot_remain_time = copy.deepcopy(robot_remain_time)
        temp_used_robot_arm = []
        no_repeat_positions = list(set(merged_product_get_procedure))
        all_product_get_procedure[procedure_num] = no_repeat_positions
        
        for position in no_repeat_positions:
            robot_arm_number = responsible_robot_arm(position, Warehouse_container_interval,first_container_x)
            '''
            consume_time ????? abs(y2 - y1) + abs(z2 - z1)
            '''
            consume_time = abs(robot_arm_info.get("exit_position")[robot_arm_number][1] - position[1]) + abs(robot_arm_info.get("exit_position")[robot_arm_number][2] - position[2])
            temp_robot_remain_time[robot_arm_number] += consume_time
            temp_used_robot_arm.append(robot_arm_number)
        
        consume_time_arr = []
        for arm_num in temp_used_robot_arm:
            consume_time_arr.append(temp_robot_remain_time[arm_num])
        all_robot_remain_time[procedure_num] = consume_time_arr
        
    for i in range(len(all_robot_remain_time)):
        all_robot_remain_time[i] = max(all_robot_remain_time[i])
    
    best_combination_index = np.argmin(all_robot_remain_time)
    
    return all_product_get_procedure,best_combination_index

'''
把排序後的訂單丟入此參數，找出能夠最早完成此訂單任務的機械手臂與商品分配方法
'''
def product_distribution_func(robot_arm_info,robot_arm_missions,items_position_dict,order,Warehouse_container_interval,first_container_x):
    
    #機器手臂使用情況
    robot_remain_time = cal_robot_time(robot_arm_info,robot_arm_missions)
    #所有商品提取組合
    all_product_combination = cal_products_cotent_combination(items_position_dict,order)
    #計算訂單撿取最佳解
    all_product_get_procedure,best_combination_index = cal_order_pic_seq(all_product_combination,robot_remain_time,Warehouse_container_interval,first_container_x)
            
    return all_product_get_procedure[best_combination_index],all_product_get_procedure,best_combination_index


def responsible_robot_arm(item_position, Warehouse_container_interval,first_container_x):
    robot_arm_number = int((item_position[0]-first_container_x)/Warehouse_container_interval)
    return robot_arm_number

'''
把排序後的訂單丟入此參數，找出能夠最早完成此訂單任務的機械手臂與商品分配方法
'''
def product_distribution_func_old(robot_arm_info,robot_arm_missions,items_position_dict,order):
    total_robot_arm_num = len(robot_arm_info.get('robot_arm_number'))
    robot_remain_time = [0]*total_robot_arm_num
    current_time = datetime.datetime.now()
    for i in range(total_robot_arm_num):
        temp_robot_arm_info = robot_arm_missions.get(str(i))
        missions = temp_robot_arm_info.get('mission_list')
        executed_time_for_first_mission = temp_robot_arm_info.get('mission_start_time') - (current_time - temp_robot_arm_info.get('mission_start_time')).total_seconds()

        for missionnum in range(len(missions)):
            if missionnum != 1:
                robot_remain_time[i] += missions[missionnum].get('mission_consume_time')
            else:
                remain_time_for_first_mission = missions[missionnum].get('mission_consume_time') - executed_time_for_first_mission
                robot_remain_time[i] += remain_time_for_first_mission

    products = order.get('content')
    arm_positions = [] #[[1, 2], [1, 3, 4], [2]]
    for product in products:
        product_id = product.get("product_id")
        temp_arm_position = list(set(items_position_dict[product_id].get('robot_arm_number')))
        arm_positions.append(temp_arm_position)
        
    '''
    ??????????????????????????
    問題
    假設分配好商品 [a,b,c] 搭配機械手臂 [1,2,3]
    但商品數量只用一個儲格不夠要用兩個儲格位置取貨才行
    
    那是不是乾脆換另一個組合 [a,b,c] [2,2,3]
    '''
    all_combinations = list(itertools.product(*arm_positions))
    all_consume_time = [[0]*total_robot_arm_num]*len(all_combinations)
    used_robot_arm = []
    for combinationnum in range(len(all_combinations)):
        combination = all_combinations[combinationnum]
        for productnum in range(len(combination)):
            product_id = products[productnum].get("product_id")
            product_info = items_position_dict.get(product_id)
            robot_arm_num = product_info.get('robot_arm_number')[combination[productnum]]
            used_robot_arm.append(robot_arm_num)
            robot_arm_index = product_info.get('robot_arm_number').index(combination[productnum])
            position =  product_info.get('position')[robot_arm_index]
            '''
            consume_time ????? abs(y2 - y1) + abs(z2 - z1)
            '''
            consume_time = abs(robot_arm_info.get("exit_position")[robot_arm_index][1] - position[1]) + abs(robot_arm_info.get("exit_position")[robot_arm_index][2] - position[2])
            all_consume_time[combinationnum][robot_arm_num] += consume_time
            
    all_consume_time_matrix = [0]*len(all_combinations)
    for consume_time_num in range(len(all_consume_time)):
        for used_robot_num in range(len(used_robot_arm)):
            all_consume_time_matrix[consume_time_num] = robot_remain_time[used_robot_arm[used_robot_num]] + all_consume_time[consume_time_num][used_robot_arm[used_robot_num]]
    best_combination_index = np.argmin(all_consume_time_matrix)
    return all_combinations[best_combination_index]

'''
根據訂單內商品分散於每個走道程度排序訂單優先序
'''
def order_priority_func(orders,items_position_dict,critical_exist_time,hot_item_score_matrix):
    '''
    訂單排序因素:
    訂單商品分散在各走道程度，但若是位於同一xyz內則算夠分散(後半部不知道怎麼加code，但是也可能儲位配置就分開了 比較不會這種情況)
    訂單存在時間
    商品熱門度
    '''
    
    order_priority_score = []
    time_score = []
    diversity_score = []
    #hot_item_score = []
    for ordernum in range(len(orders)):
        order = orders[ordernum]
        start_time = order.get('datetime')
        current_time = datetime.datetime.now()
        exist_time = (current_time - start_time).total_seconds()
        time_score.append(critical_exist_time**(exist_time/critical_exist_time))
        products = order.get('content')
        
        arm_positions = [] #[[1, 2], [1, 3, 4], [2]]
        for product in products:
            product_id = product.get("product_id")
            temp_arm_position = items_position_dict[product_id].get('robot_arm_number')
            arm_positions.append(list(set(temp_arm_position)))
        
        all_combinations = list(itertools.product(*arm_positions)) #[(1, 1, 2), (1, 3, 2), (1, 4, 2), (2, 1, 2), (2, 3, 2), (2, 4, 2)]
        all_possible_arms_for_orderx = set(sum(arm_positions,[])) #[1, 2, 3, 4]
        max_diverse_score = 0
        for i in range(len(all_combinations)):
            temp_diverse_score = len(set(all_combinations[i]))/len(all_possible_arms_for_orderx)
            if temp_diverse_score > max_diverse_score:
                max_diverse_score = temp_diverse_score
        diversity_score.append(max_diverse_score)
        
        '''
        time score templorily ignored
        '''
        #order_priority_score.append(diversity_score[ordernum]*1 + hot_item_score_matrix[ordernum]*1 + time_score[ordernum]*0.5)
        order_priority_score.append(diversity_score[ordernum]*1 + hot_item_score_matrix[ordernum]*1)

    sort_index = sorted(range(len(order_priority_score)), key = lambda k : order_priority_score[k])
    new_orders = []
    for index in reversed(sort_index):
        new_orders.append(orders[index])
    
    return new_orders

'''
北科大訂單相似度排序
'''
def order_similarity_func(orders):
    '''
    訂單相似度分析，高的排前面
    orders : 存每個訂單
    orders:[order1,order2]
    orderX:
        {
                order_id:
                datetime:
                content:
                    [
                            {product_id","quantity","x","y","z","product_weight(g)","product_lenth(cm)","product_width(cm)","product_height(cm)"}
                            {product_id","quantity","x","y","z","product_weight(g)","product_lenth(cm)","product_width(cm)","product_height(cm)"}
                            {product_id","quantity","x","y","z","product_weight(g)","product_lenth(cm)","product_width(cm)","product_height(cm)"}
                    ]
        }
    '''
    df3 = pd.read_csv('data2.csv') #讀取輸入資料
    df3 = df3[["order_id","product_id","quantity","x","y","z","product_weight(g)","product_lenth(cm)","product_width(cm)","product_height(cm)"]]
    df3 = np.array(df3)
    
    array_order_id = df3[:,0] #order_id
    array_product_id = df3[:,1] #product_id
    order_name=[] #判斷有哪些訂單名稱
    for i in range(len(array_order_id)):  
        if array_order_id[i] not in order_name:
            order_name.append(array_order_id[i])
        else:
            pass
    #將order_name變成二維陣列
    b=[[i for i in ii.split(',')] for ii in order_name]
    
    if len(order_name) != 1:
        #判斷訂單裡有些商品
        product_of_order=[[] for i in range(len(order_name))] #訂單裡有哪些商品
        for i in range(len(order_name)):
            for j in range(len(array_order_id)):
                if array_order_id[j] == b[i][0]:
                    product_of_order[i].append(array_product_id[j])
                else:
                    pass
    
        #將相似度高的訂單擺放前後
        jaccard=[] #儲存jaccard數值
        v=1
        for i in range(len(order_name)-1):
            
            for j in range(i+1, len(order_name)):
    
                jaccard.append(jaccard_similarity(product_of_order[i],product_of_order[j]))
                if len(jaccard) == (len(order_name)-1-i):
                    order_jaccard=np.array(jaccard).reshape(len(jaccard),1)
                    order_jaccard=order_jaccard.tolist()
                    
                    for s in range(len(order_jaccard)):
                        ss = s+i+1
                        order_jaccard[s].append(order_name[i])
                        order_jaccard[s].append(order_name[ss])
                    order_jaccard_list=sorted(order_jaccard,key=(lambda x:x[0]),reverse=True)
                    or1=order_name.index(order_jaccard_list[0][1])
                    or2=order_name.index(order_jaccard_list[0][2])
                    #交換位置
                    product_of_order[or1+v], product_of_order[or2] = product_of_order[or2],product_of_order[or1+v]
                    order_name[or1+v], order_name[or2] = order_name[or2],order_name[or1+v]
                    v=v+1
                    jaccard=[]
                v=1
                            
        #依照新訂單排序排列訂單
        new_order=[]
        for i in range(len(order_name)):
            for j in range(len(array_order_id)):
                
                if order_name[i] == array_order_id[j]:
                    array_order_idd=df3[(j),:]
                    aa=array_order_idd.tolist()
                    new_order.append(aa)
                else:
                    pass       
        new_order=np.array(new_order)
    return new_order
'''
北科大訂單相似度排序
'''
def jaccard_similarity(x,y):    #jaccard_similarity相似度分析公式
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    return intersection_cardinality/float(union_cardinality)

'''
生成訂單
'''
def order_produce_func(order_length, content_max, product_id_max,amount_max):
    orders = []
    for order_num in range(order_length):
        order = {}
        order_id = str(order_num)
        amount = random.randint(1,amount_max)
        order["order_id"] = order_id
        order["datetime"] = datetime.datetime.now()
        order["content"] = []
        content_length = random.randint(1,content_max)
        for content_num in range(content_length):
            temp_content = {}
            product_id = str(random.randint(1,product_id_max))
            amount = random.randint(1,amount_max)
            temp_content["product_id"] = product_id
            temp_content["amount"] = amount
            order["content"].append(temp_content)
        orders.append(order)
        
    return orders
    
product_id_max = 20
amount_max = 5
orders = order_produce_func(10,3,product_id_max,amount_max)
#new_orders = order_priority_func(orders,items_position_dict,12 * 60 * 60,hot_item_score_matrix)

robot_arm_info = {'robot_arm_number':[],'exit_position':[]}
robot_arm_total_number = 50
for i in range(robot_arm_total_number):
    temp_robot_arm_total_number = i
    exit_position = (0.5+i,15,0)
    robot_arm_info["robot_arm_number"].append(temp_robot_arm_total_number)
    robot_arm_info["exit_position"].append(exit_position)
    

robot_arm_missions = {
                        '0':{
                                "mission_start_time":datetime.datetime.now(),
                                "mission_list":[
                                                    {
                                                    "order_id":"1234567",
                                                    "mission_consume_time":5,
                                                    "mission_position":(1,1,1,0)
                                                    },
                                                    {
                                                    "order_id":"1234568",
                                                    "mission_consume_time":3,
                                                    "mission_position":(1,1,1,2)
                                                    }
                                                ]
                            },
                        '1':{
                                "mission_start_time":datetime.datetime.now(),
                                "mission_list":[
                                                    {
                                                    "order_id":"1234569",
                                                    "mission_consume_time":2,
                                                    "mission_position":(1,1,1,4)
                                                    },
                                                    {
                                                    "order_id":"1234570",
                                                    "mission_consume_time":1,
                                                    "mission_position":(1,1,1,1)
                                                    }
                                                ]
                            },
                    }

for i in range(2,robot_arm_total_number):
    robot_arm_missions[str(i)] = {"mission_start_time":datetime.datetime.now(),"mission_list":[]}

                                

highest_layer = 3
longest_path = 50
Warehouse_width = 6
Warehouse_length = 3
Warehouse_height = highest_layer
x_interval = 2
y_interval = 2
z_interval = 2
x_initial = 4
y_initial = 0
z_initial = 2
positions_in_onexyz = 4 #一個儲格有4個位置

Warehouse_dict = {}
# =============================================================================
# Warehouse_dict = Warehouse_items(Warehouse_dict,1,1,1,0,"Chocolate",3,"條")
# Warehouse_dict = Warehouse_items(Warehouse_dict,1,1,1,1,"Milk",4,"罐")
# Warehouse_dict = Warehouse_items(Warehouse_dict,1,1,1,2,None,None,None)
# Warehouse_dict = Warehouse_items(Warehouse_dict,1,1,1,3,"Candy",3,"包")
# Warehouse_dict.get((1,1,1,0))
# =============================================================================
for width_num in range(Warehouse_width):
    for length_num in range(Warehouse_length):
        for height_num in range(highest_layer):
            for i in range(positions_in_onexyz):
                temp_product_id = random.randint(1,product_id_max)
                temp_amount = random.randint(1,amount_max*2)
                Warehouse_items(Warehouse_dict,width_num,length_num,height_num,i,str(temp_product_id),str(temp_product_id),temp_amount,"條")


Warehouse_container_interval = 1 #貨架間距
first_container_x = 0 #第一個貨架的中心x位置
items_position_dict = {}
items_position_dict = items_positions(Warehouse_dict,items_position_dict,1,-0.5)
# =============================================================================
# items_position_dict = items_positions_old(items_position_dict,"14050145",1,1,1,3,Warehouse_container_interval,first_container_x)
# items_position_dict = items_positions_old(items_position_dict,"14050145",8,1,1,4,Warehouse_container_interval,first_container_x)
# items_position_dict = items_positions_old(items_position_dict,"14050145",13,1,1,5,Warehouse_container_interval,first_container_x)
# items_position_dict = items_positions_old(items_position_dict,"68030025",20,1,1,11,Warehouse_container_interval,first_container_x)
# =============================================================================
item_time_score = []
for i in range(4):
    item_time_score.append(News_Feed_func(10+5*i,20,0.6,1,20,40,1,4))


item_similarity_score = []
for i in range(4):
    item_similarity_score.append(News_Feed_func(10,20,0.2*(i+1),1,20,40,1,4))
    
item_pathlength_score = []
for i in range(4):
    item_pathlength_score.append(News_Feed_func(10,20,0.6,1,10*(i+1),40,1,4))

item_layer_score = []
for i in range(4):
    item_layer_score.append(News_Feed_func(10,20,0.6,1,20,40,1*(i+1),4))
    
#new_order = order_similarity_func(0)
hot_item_score_matrix = [1]*len(orders)
new_orders = order_priority_func(orders,items_position_dict,12*60*60,hot_item_score_matrix)
order_len = len(new_orders)
ordernum = 0 
order = new_orders[ordernum]
result = product_distribution_func(robot_arm_info,robot_arm_missions,items_position_dict,order,Warehouse_container_interval,first_container_x)
# =============================================================================
# for ordernum in range(order_len):
#     order = new_orders[ordernum]
#     order_priority = ((order_len - ordernum)/order_len)
#     content = order.get("content")
#     for productnum in range(len(content)):
#         product = content[productnum]
#         news_feed_score_matrix = []
#         start_time = order.get("datetime")
#         exist_time = (datetime.datetime.now() - start_time).total_seconds()
#         product_id = product.get("product_id")
#         product_info = items_position_dict.get(product_id)
#         possible_arms = list(set(product_info.get('robot_arm_number')))
#         
#         '''
#         choose the most suitable robot arm to pick this product
#         '''
#         for choice_num in range(len(possible_arms)):
#             chosen_arm = possible_arms[choice_num]
#             path_length = (robot_arm_info.get('exit_position')[chosen_arm][1] - product_info.get('position')[choice_num][1])
#             item_layer = product_info.get('position')[choice_num][2]
#             news_feed_score = News_Feed_func(exist_time,12*60*60,0.6,order_priority,path_length,longest_path,item_layer,highest_layer)
#             news_feed_score_matrix.append(news_feed_score)
#         choice_result = possible_arms[np.argmax(news_feed_score_matrix)]
# =============================================================================

