import os
from django.shortcuts import render, redirect
# from .forms import AlarmForm
from .models import Operator,PressureAnalysis,AlarmDetails
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
from django.http import HttpResponse
import json
import datetime
import pandas as pd
from pymodbus.client import ModbusTcpClient
import pyodbc
import threading
from termcolor import colored
import csv
from pymodbus.client.mixin import ModbusClientMixin
import struct


#############################################################################################################################

database_access_logging = False
handler_execution_logging = False
exception_logging = False
log_function_execution = True

############################Decorators#######################################################################################


def log(func):
    def wrapper(*args, **kwargs):
        if log_function_execution:
            print(colored(f"Executing function : {func.__name__}", "yellow"))
            result = func(*args, **kwargs)
            print(colored(f"Function completed : {func.__name__}","yellow"))
            return result
        else:
            return func(*args, **kwargs)
    return wrapper


###############################Creating Log Files################################################################################
timestamp = str(datetime.datetime.now())
timestamp = timestamp.split(" ")
date = timestamp[0]
time = timestamp[1]
time = time.split(":")
time = f"{time[0]}-{time[1]}-{time[2][0:2]}"
timestamp = f"D{date}T{time}"

print(f"timestamp : {timestamp}")
if database_access_logging:
    with open(f"files/DatabaseAccessLogs{timestamp}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date","Time","Query Id", "Type", "Query", "Rows Returned","Json Conversion"])
        print("logs file created")

if handler_execution_logging:
    with open(f"files/HandlerExecutionLogs{timestamp}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date","Time", "Handler Name"])
        print("logs file created")
    
if exception_logging:
    with open(f"files/ExceptionLogs{timestamp}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date","Time","Id", "Function Name", "Exception Type", "Developer Description", "Exception Message"])
        print("logs file created")


with open(f"files/HMILogs{timestamp}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Type", "address", "value"])
        print("logs file created")
        
#################################Logging functions#################################################################################

tracker = 1
lock = threading.Lock()

def log_database_access(type,query,rowcount,jsonconversion):
    global timestamp, tracker
    if database_access_logging:
        with lock:
            querytime = str(datetime.datetime.now()).split(" ")
            date = querytime[0]
            time = querytime[1]
            with open(f"files/DatabaseAccessLogs{timestamp}.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([date,time,tracker,type,query,rowcount,jsonconversion])
            print(colored(f"Query executed and logged : {tracker}", "green"))
            tracker += 1
    


handler_execution_tracker = 1
handler_execution_lock = threading.Lock()

def log_handler_execution(name):
    global timestamp
    if handler_execution_logging:
        with handler_execution_lock:
            querytime = str(datetime.datetime.now()).split(" ")
            date = querytime[0]
            time = querytime[1]
            with open(f"files/HandlerExecutionLogs{timestamp}.csv", mode="a", newline="")  as file:
                writer = csv.writer(file)
                writer.writerow([date, time, name])
            print(colored(f"Handler executed : {name}", "blue"))
            
exception_tracker = 1
exception_lock = threading.Lock()

def log_exception(function_name, excpetion_type, dev_desc, exception_msg):
    global timestamp, exception_tracker
    if exception_logging:
        with exception_lock:
            querytime = str(datetime.datetime.now()).split(" ")
            date = querytime[0]
            time = querytime[1]
            with open(f"files/ExceptionLogs{timestamp}.csv", mode="a", newline="")  as file:
                writer = csv.writer(file)
                writer.writerow([date, time, exception_tracker, function_name, excpetion_type, dev_desc, exception_msg])
            exception_tracker += 1
            print(colored(f"[{exception_tracker}] Exception Logged : [{function_name}] : [{excpetion_type}] : {dev_desc} - {exception_msg}", "red"))

###################################################################################################################################


runsrc = True

r12connection = False
is_data_loaded = False
available_tests = []

def select_query(query,param=[], convert_to_json = True):
    global tracker, database_access_logging
    param = tuple(param)
    with connection.cursor() as c:
        c.execute(query,param)
        data = c.fetchall()
        rowcount = len(date)
        if (convert_to_json):
            columns = [col[0] for col in c.description]
            data = [dict(zip(columns, row)) for row in data]
    if (database_access_logging):
        threading.Thread(target=log_database_access, args=("Select",query % param,rowcount,convert_to_json)).start()
    return data

def update_query(query,params = []):
    global tracker, database_access_logging
    params = tuple(params)
    with connection.cursor() as c:
        c.execute(query,params)
    if(database_access_logging):
        threading.Thread(target=log_database_access, args=("Update",query % params, 0, False)).start()


def connect_to_r12():
    global r12connection
    data = select_query("select r12_connection, fm_arca_host_address, fm_arca_port, fm_arca_database, fm_arca_option, fm_arca_username, fm_arca_password from configuration_tbl")
    data = data[0]
    server = data["fm_arca_host_address"]  # or '127.0.0.1' for a local server
    database = data["fm_arca_database"]
    username = data["fm_arca_username"]
    password = data["fm_arca_password"]
    option = data["fm_arca_option"]
    # connection_string = f'DRIVER={{MySQL ODBC 9.0 ANSI Driver}};SERVER={server};DATABASE={database};UID={username};PASSWORD={password};OPTION={option}'
    connection_string = f'DRIVER={{MySQL ODBC 9.0 ANSI Driver}};SERVER=localhost;DATABASE=sing_ssd;UID=root;PASSWORD=;'
    if(data["r12_connection"] == '1'):
        try:
            r12connection = pyodbc.connect(connection_string)
            print(colored("R12 Database Connection successful", "green"))
            return "green"
    
        except pyodbc.Error as e:
            threading.Thread(target=log_exception, args=("connect_to_r12",type(e).__name__, "Error while connecting to R12 database", e)).start()
            print(colored(f"[Error] : [{type(e).__name__}] : Error while connecting to database : {e}"))
            return "red"
    else:
        return "grey"

def checkr12connection(request):
    threading.Thread(target=log_handler_execution, args=("checkr12connection",)).start()
    global is_data_loaded
    status = connect_to_r12()
    if (status == "green"):
        if not is_data_loaded:
            getting_data_from_r12()
    return HttpResponse(status)
    

tesleadsmartsyncx = None
isconnected = None
def checkhmiconnection(request):
    threading.Thread(target=log_handler_execution, args=("checkhmiconnection",)).start()
    global tesleadsmartsyncx, isconnected
    data = select_query(f"select hmi_connection, hmi_ip_address, hmi_port from configuration_tbl")
    data = data[0]
    
    if (data["hmi_connection"] == '1'):
        if not isconnected:
            tesleadsmartsyncx = ModbusTcpClient(data["hmi_ip_address"])
            isconnected = tesleadsmartsyncx.connect()
            if (isconnected):
                return HttpResponse("green")
            else:
                return HttpResponse("red")
        else:
            return HttpResponse("green")
    else:
        return HttpResponse("grey")


def checkalarmsystemconnection(request):
    threading.Thread(target=log_handler_execution, args=("checkalarmsystemconnection",)).start()
    data = select_query("select alarm_system from configuration_tbl")
    data = data[0]["alarm_system"]
    if (data == '1'):
        return HttpResponse("green")
    else:
        return HttpResponse("red")


def getting_data_from_r12():
    global is_data_loaded
    global r12connection
    update_query("truncate table operator_tbl")
    update_query("truncate table testing_parameters_t")
    cellid = select_query("select cell_id from configuration_tbl")[0]["cell_id"]
    operator_data = r12connection.execute(f"select * from sing_ssd.xxfmmfg_scada_operators_t where cell_id = {cellid}")
    operator_data = operator_data.fetchall()
    
    for row in operator_data:
        update_query("insert into operator_tbl (cell_id, opr_token,password, first_name, last_name) values (%s,%s,%s,%s,%s)", row)
        
    
    tp_data = r12connection.execute(f"select * from sing_ssd.xxfmmfg_trc_testing_parameters_t where cell_id = {cellid}")
    tp_data = tp_data.fetchall()
    for row in tp_data:
        update_query("insert into testing_parameters_t values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row)
    
    is_data_loaded = True
        
    
    



@log
def admin_login_page(request):
    threading.Thread(target=log_handler_execution, args=("admin_login_page",)).start()
    # global runsrc
    # if runsrc:
    #     threading.Thread(target=main_thread).start()
    #     runsrc = False
    return render(request, 'Admin_Login.html' , {"r12connection": r12connection})

@log
def r12_login_page(request):
    threading.Thread(target=log_handler_execution, args=("r12_login_page",)).start()
    # Fetch all operators from the database
    operators = Operator.objects.all()
    # Render the R12_Login.html template with the fetched operators
    return render(request, 'R12_Login.html', {'operators': operators})

def r12connection_import_data():
    connect_to_r12()
    getting_data_from_r12()
    
threading.Thread(target=r12connection_import_data).start()

@log
def r12_dashboardview(request):
    threading.Thread(target=log_handler_execution, args=("r12_dashboardview",)).start()
    global current_loggedin_user
    return render(request, "R12_Dashboard.html",{'logged_user' : current_loggedin_user})

current_loggedin_user = "User"
@log
def loginr12(request):
    threading.Thread(target=log_handler_execution, args=("loginr12",)).start()
    global current_loggedin_user
    id = request.POST.get("id")
    password = request.POST.get("password")

    with connection.cursor() as c:
        data = select_query("select password from operator_tbl where id = %s", [id],False)[0][0]
        if (password == data):
            name = select_query("select first_name, last_name, cell_id, opr_token from operator_tbl where id = %s", [id],False)
            current_loggedin_user = f"{name[0][0]} {name[0][1]}"
            update_query("truncate table logged_user")
            update_query("insert into logged_user values (%s,%s,%s,%s)",[name[0][2],name[0][3],name[0][0],name[0][1]])
            return render(request, "R12_Dashboard.html",{"logged_user" : current_loggedin_user})
    
    operators = Operator.objects.all()
    # Render the R12_Login.html template with the fetched operators
    return render(request, 'R12_Login.html', {'operators': operators, 'error':"Invalid Password"})


def user_dashboard(request):
    threading.Thread(target=log_handler_execution, args=("user_dashboard",)).start()
    if request.method == "POST" and request.POST.get("username") == "user" and request.POST.get("password") == "user":
        return render(request, "Admin_Page.html", {'type': "user"})
    return redirect('user_login')

@log
def admin_product_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_product_view",)).start()
    data = select_query("select product_id, product_name, product_description, id from product",[],False)
    
    return render(request, "Admin_Product.html", {'data':data})

@log
def admin_dashboard_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_dashboard_view",)).start()
    return render(request, "Admin_Dashboard.html")

@log
def admin_analytics_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_analytics_view",)).start()
    with connection.cursor() as c:
        results = select_query("select id, valve_serial_number, valve_status, set_pressure, set_time from pressure_analysis",[], False)
    return render(request, "Admin_Analytics.html",{'pressure_data' : results})

@log
def test_serial_form(request):
    threading.Thread(target=log_handler_execution, args=("test_serial_form",)).start()
    
    with connection.cursor() as cursor:
        data = select_query("select cell_id from configuration_tbl",[],False)
    return render(request, "TestSerialForm.html",{'cell_id': data[0][0]})

@log
def r12_live_status(request):
    threading.Thread(target=log_handler_execution, args=("r12_live_status",)).start()
    global current_loggedin_user
    with connection.cursor() as c:
        result = select_query("select s.valve_serial_number, t.driving_param1_value, t.driving_param2_value from serial_tbl s join temp_testing_parameters_t t on s.valve_serial_number = t.serial_number",[],False)[0]
        data = {
            'valve_serial_number': result[0],
            'sizeclass': f"{result[1]} - {result[2]}",
            'loggedin_user' : current_loggedin_user
        }
        
    return render(request, "R12_Live_Status.html",{'datas' : data})

@log
def admin_alarm_system_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_alarm_system_view",)).start()
    with connection.cursor() as cursor:
        result = select_query("select * from alarm_details",[],False)
    data = [{'id': row[0], 'alarm_id': row[1], 'alarm_name': row[2]} for row in result]

    return render(request, "Admin_Alarm_System.html", {'data':data})

@log
def admin_configuration_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_configuration_view",)).start()
    data = select_query("select * from configuration_tbl")
    return render(request, "Admin_Configuration.html",{'data': data[0]})

@log
def admin_report_view(request):
    threading.Thread(target=log_handler_execution, args=("admin_report_view",)).start()
    with connection.cursor() as c:
        results = select_query("select id, valve_serial_number, case when valve_status = 1 then 'Test Passed' when valve_status = 2 then 'Running' when valve_status = 3 then 'Ready to test' else 'Test Failed' end as valve_status, set_pressure, set_time, type_name from pressure_analysis")
        
    return render(request, "Admin_Report.html", {'pressure_data':results})


@log
def admin_dashboard(request):
    threading.Thread(target=log_handler_execution, args=("admin_dashboard",)).start()
    if request.method == "POST" and request.POST.get("username") == "admin" and request.POST.get("password") == "admin":
        cellid = select_query("select cell_id from configuration_tbl",[],False)[0][0]
        update_query("insert into logged_user values (%s,%s,%s,%s)",[cellid, "1234","Admin",""])
        return render(request, "Admin_Dashboard.html")

    return redirect('admin_login')

@log
def alarm_system_view(request):
    threading.Thread(target=log_handler_execution, args=("alarm_system_view",)).start()
    data = select_query("select * from alarm_details")
    return JsonResponse(data, safe=False)

def getalarmbyid(request):
    threading.Thread(target=log_handler_execution, args=("getalarmbyid",)).start()
    id = request.POST.get("id")
    data = select_query(f"select * from alarm_details where id = {id}")
    return JsonResponse(data[0],safe=False)
    

def addalarmtodatabase(request):
    threading.Thread(target=log_handler_execution, args=("addalarmtodatabase",)).start()
    id = int(request.POST.get("id"))
    if (id == 0):
        with connection.cursor() as c:
            update_query("insert into alarm_details (alarm_id,alarm_name) values (%s,%s)",[request.POST.get("alarm_id"),request.POST.get("alarm_name")])
    else:
        with connection.cursor() as c:
            update_query("update alarm_details set alarm_id = %s, alarm_name = %s where id=%s", [request.POST.get("alarm_id"), request.POST.get("alarm_name"), id])
    return redirect("admin_alarm_system")

def deletealarm(request):
    threading.Thread(target=log_handler_execution, args=("deletealarm",)).start()
    id = request.POST.get("id")
    update_query(f"delete from alarm_details where id = {id}")
    return HttpResponse("deleted")

@log
def test_details(request):
    threading.Thread(target=log_handler_execution, args=("test_details",)).start()
    return render(request, "Test_Details.html")

@log
def live_status(request):
    threading.Thread(target=log_handler_execution, args=("live_status",)).start()
    global current_loggedin_user
    update_query("truncate table temp_pressure_analysis")
    serial = request.POST.get("sn")
    update_query("update serial_tbl set valve_serial_number = %s",[serial])
    update_query("insert into master_serial (valve_serial_no) values (%s)",[serial])
    product_id = request.POST.get("product")

    
    product_details = select_query("select * from product where id = %s",[product_id])[0]
    cell_id = select_query("select cell_id from configuration_tbl")[0]["cell_id"]
    
    product_name = product_details["product_name"]
    pressure_uom = "BAR G"
    holding_time_uom = "Secs"
    driving_param1_desc = "SIZE"
    driving_param1_value = product_details["size"]
    driving_param2_desc = "CLASS RATING"
    driving_param2_value = product_details["class"]
    driving_param3_desc = "FLANGED STD"
    driving_param3_value = product_details["flanged_type"]
    driving_param4_desc = "ACTION"
    driving_param4_value = product_details["actuator_type"]
    
    
    update_query("truncate table temp_testing_parameters_t")
    for testid in [424,420,419,421]:
        if (testid == 424):
            test_name = "Arca Air Shell"
            test_media = "Air"
            pressure_low_limit = product_details["ashell_set_pressure"]
            pressure_high_limit = product_details["ashell_set_pressure"]
            holding_time_value = product_details["ashell_set_duration"]
        elif (testid == 420):
            test_name = "Arca Air Seat"
            test_media = "Air"
            pressure_low_limit = product_details["aseat_set_pressure"]
            pressure_high_limit = product_details["aseat_set_pressure"]
            holding_time_value = product_details["aseat_set_duration"]
        elif (testid == 419):
            test_name = "Arca Hydro Shell"
            test_media = "Water"
            pressure_low_limit = product_details["hshell_set_pressure"]
            pressure_high_limit = product_details["hshell_set_pressure"]
            holding_time_value = product_details["hshell_set_duration"]
        elif (testid == 421):
            test_name = "Arca Hydro Seat"
            test_media = "Water"
            pressure_low_limit = product_details["hseat_set_pressure"]
            pressure_high_limit = product_details["hseat_set_pressure"]
            holding_time_value = product_details["hseat_set_duration"]
            
        update_query("insert into temp_testing_parameters_t (cell_id, test_id, test_name, test_media, serial_number, pressurelowlimit, pressurehighlimit, pressure_uom, holdingtime_value, holdingtime_uom, driving_param1_desc, driving_param1_value,driving_param2_desc, driving_param2_value,driving_param3_desc, driving_param3_value,driving_param4_desc, driving_param4_value) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                     [cell_id, testid, test_name,test_media, serial, pressure_low_limit, pressure_high_limit, pressure_uom, holding_time_value, holding_time_uom, driving_param1_desc, driving_param1_value, driving_param2_desc, driving_param2_value, driving_param3_desc, driving_param3_value, driving_param4_desc, driving_param4_value])
        
        
    
    with connection.cursor() as c:
        result = select_query("select s.valve_serial_number, t.driving_param1_value, t.driving_param2_value from serial_tbl s join temp_testing_parameters_t t on s.valve_serial_number = t.serial_number",[],False)[0]
        data = {
            'valve_serial_number': result[0],
            'sizeclass': f"{result[1]} - {result[2]}",
            'loggedin_user' : current_loggedin_user
        }
    return render(request, "Live_Status.html", {'datas': data, 'product': product_name})


def add_product(request):
    threading.Thread(target=log_handler_execution, args=("add_product",)).start()
    id = request.POST.get("id")
    product_id = request.POST.get("product_id")
    product_name = request.POST.get("product_name")
    product_description = request.POST.get("product_description")
    size = request.POST.get("size")
    classs = request.POST.get("class")
    type = request.POST.get("type")
    hshell_set_pressure = request.POST.get("hshell_set_pressure")
    hshell_set_holding_time = request.POST.get("hshell_set_holding_time")
    hshell_set_duration = request.POST.get("hshell_set_duration")
    hseat_set_pressure = request.POST.get("hseat_set_pressure")
    hseat_set_holding_time = request.POST.get("hseat_set_holding_time")
    hseat_set_duration = request.POST.get("hseat_set_duration")
    ashell_set_pressure = request.POST.get("ashell_set_pressure")
    ashell_set_holding_time = request.POST.get("ashell_set_holding_time")
    ashell_set_duration = request.POST.get("ashell_set_duration")
    aseat_set_pressure = request.POST.get("aseat_set_pressure")
    aseat_set_holding_time = request.POST.get("aseat_set_holding_time")
    aseat_set_duration = request.POST.get("aseat_set_duration")
    flengedtype = request.POST.get("flangedtype")
    actuatortype = request.POST.get("actuatortype")
    
    if (id == '0'):
        with connection.cursor() as cursor:
            update_query("INSERT INTO product (product_id, product_name, product_description, size, class, type, hshell_set_pressure, hshell_set_holding_time, hshell_set_duration, hseat_set_pressure, hseat_set_holding_time, hseat_set_duration, ashell_set_pressure, ashell_set_holding_time, ashell_set_duration, aseat_set_pressure, aseat_set_holding_time, aseat_set_duration, flanged_type, actuator_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,%s,%s)",[product_id, product_name, product_description, size, classs, type, hshell_set_pressure, hshell_set_holding_time, hshell_set_duration, hseat_set_pressure, hseat_set_holding_time, hseat_set_duration, ashell_set_pressure, ashell_set_holding_time, ashell_set_duration, aseat_set_pressure, aseat_set_holding_time,aseat_set_duration, flengedtype, actuatortype])
    else:
        with connection.cursor() as c:
            update_query("update product set product_id = %s, product_name=%s,product_description = %s,size=%s,class=%s,type=%s, hshell_set_pressure=%s, hshell_set_holding_time=%s, hshell_set_duration=%s,hseat_set_pressure=%s, hseat_set_holding_time=%s, hseat_set_duration=%s, ashell_set_pressure=%s, ashell_set_holding_time=%s, ashell_set_duration=%s, aseat_set_pressure=%s, aseat_set_holding_time=%s, aseat_set_duration=%s, flanged_type = %s, actuator_type = %s where id = %s",[product_id, product_name, product_description, size, classs, type, hshell_set_pressure, hshell_set_holding_time, hshell_set_duration, hseat_set_pressure, hseat_set_holding_time, hseat_set_duration, ashell_set_pressure, ashell_set_holding_time, ashell_set_duration, aseat_set_pressure, aseat_set_holding_time,aseat_set_duration, flengedtype, actuatortype,id])
    return redirect("admin_product")


def deleteproduct(request):
    threading.Thread(target=log_handler_execution, args=("deleteproduct",)).start()
    id = request.POST.get("id")
    update_query(f"delete from product where id = {id}")
    return HttpResponse("deleted")



valve_size = None

def airshellfunction(request):
    threading.Thread(target=log_handler_execution, args=("airshellfunction",)).start()
    with connection.cursor() as cursor:
        serial_number = select_query("select valve_serial_number from serial_tbl",[],False)[0][0]
        tpa_pa_insert(serial_number, 1)
        # cursor.execute("select * from testing_parameters_t where serial_number=%s and test_name='Arca Air Shell'",[serial_number])
        # data = cursor.fetchall()
        # pressure_unit = data[0][19]
        # get_valve_size = data[0][42]
        # print("--------------------------------------------")
        # print(get_valve_size)
        # if (get_valve_size == '25 NB (1")'):
        #     valve_size = 3
        # elif (get_valve_size == '40 NB (1 1/2")'):
        #     valve_size = 4
        # elif (get_valve_size == '50 NB (2")'):
        #     valve_size = 5
        # elif (get_valve_size == '65 NB (2 1/2")'):
        #     valve_size = 6
        # elif (get_valve_size == '15 NB (1/2")'):
        #     valve_size = 1
        
        # get_valve_class = data[0][44]
        # if (get_valve_class == "#150"):
        #     valve_class = 150
        # elif (get_valve_class == "#300"):
        #     valve_class = 300

        # tested_by = "F1636"

        # cursor.execute("update pressure_analysis set status=0 and cycle_complete='0' where status=1 and cycle_complete='1'")

        # test_type = 1
        # test_type_name = "Air Shell"
        # set_pressure = data[0][18]
        # set_time_unit = data[0][21]
        # set_time = data[0][20]
        # write_hmi = 0
        # status = 1
        # station_status = 1
        # now = datetime.datetime.now()
        # cur_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        # cal_due_hydro_1 = '0000-00-00 00:00:00'
        # cal_due_hydro_2 = "0000-00-00 00:00:00"
        # cal_due_air_1 = "0000-00-00 00:00:00"
        # cal_due_air_2 = "0000-00-00 00:00:00"
        # cal_due_others_1 = "0000-00-00 00:00:00"
        # cal_due_others_2 = "0000-00-00 00:00:00"
        # cal_due_others_3 = "0000-00-00 00:00:00"
        # cal_done_hydro_1 = "0000-00-00 00:00:00"
        # cal_done_hydro_2 = "0000-00-00 00:00:00"
        # cal_done_air_1 = "0000-00-00 00:00:00"
        # cal_done_air_2 = "0000-00-00 00:00:00"
        # cal_done_others_1 = "0000-00-00 00:00:00"
        # cal_done_others_2 = "0000-00-00 00:00:00"
        # cal_done_others_3 = "0000-00-00 00:00:00"
        # cal_due_wrench = "0000-00-00 00:00:00"
        # created_on = now.strftime("%Y-%m-%d %H:%M:%S")
        # cursor.execute("select hmi_ip_address from configuration_tbl")
        # ip_address = cursor.fetchall()[0][0]
        # cursor.execute("insert into pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, date_time, type_code, type_name, ip_address, created_on) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [set_pressure, pressure_unit, valve_size, valve_class, tested_by, serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, cur_datetime, test_type, test_type_name ,ip_address, created_on])



        # print("pressure unit: " + pressure_unit)
        # print(f"valve size : {valve_size}")
        # print(f"valve class : {valve_class}")
        # print(f"tested by: {tested_by}")
        # print(f"ip address: {ip_address}")
        # # cursor.execute("insert into change_test_tbl values ('123','Arca Airshell',1)")
    return HttpResponse("created")
    

def airseatfunction(request):
    threading.Thread(target=log_handler_execution, args=("airseatfunction",)).start()
    global valve_size
    with connection.cursor() as cursor:
        
        serial_number = select_query("select valve_serial_number from serial_tbl",[],False)[0][0]
        tpa_pa_insert(serial_number, 4)
        # cursor.execute("select * from testing_parameters_t where serial_number=%s and test_name='Arca Air Seat'",[serial_number])
        # data = cursor.fetchall()
        # pressure_unit = data[0][19]
        # get_valve_size = data[0][42]
        # print("--------------------------------------------")
        # print(get_valve_size)
        # if (get_valve_size == '25 NB (1")'):
        #     valve_size = 3
        # elif (get_valve_size == '40 NB (1 1/2")'):
        #     valve_size = 4
        # elif (get_valve_size == '50 NB (2")'):
        #     valve_size = 5
        # elif (get_valve_size == '65 NB (2 1/2")'):
        #     valve_size = 6
        # elif (get_valve_size == '15 NB (1/2")'):
        #     valve_size = 1
        
        # get_valve_class = data[0][44]
        # if (get_valve_class == "#150"):
        #     valve_class = 150
        # elif (get_valve_class == "#300"):
        #     valve_class = 300

        # tested_by = "F1636"

        # cursor.execute("update pressure_analysis set status=0 and cycle_complete='0' where status=1 and cycle_complete='1'")

        # test_type = 4
        # test_type_name = "Air Seat"
        # set_pressure = data[0][18]
        # set_time_unit = data[0][21]
        # set_time = data[0][20]
        # write_hmi = 0
        # status = 1
        # station_status = 1
        # now = datetime.datetime.now()
        # cur_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        # cal_due_hydro_1 = '0000-00-00 00:00:00'
        # cal_due_hydro_2 = "0000-00-00 00:00:00"
        # cal_due_air_1 = "0000-00-00 00:00:00"
        # cal_due_air_2 = "0000-00-00 00:00:00"
        # cal_due_others_1 = "0000-00-00 00:00:00"
        # cal_due_others_2 = "0000-00-00 00:00:00"
        # cal_due_others_3 = "0000-00-00 00:00:00"
        # cal_done_hydro_1 = "0000-00-00 00:00:00"
        # cal_done_hydro_2 = "0000-00-00 00:00:00"
        # cal_done_air_1 = "0000-00-00 00:00:00"
        # cal_done_air_2 = "0000-00-00 00:00:00"
        # cal_done_others_1 = "0000-00-00 00:00:00"
        # cal_done_others_2 = "0000-00-00 00:00:00"
        # cal_done_others_3 = "0000-00-00 00:00:00"
        # cal_due_wrench = "0000-00-00 00:00:00"
        # created_on = now.strftime("%Y-%m-%d %H:%M:%S")
        # cursor.execute("select hmi_ip_address from configuration_tbl")
        # ip_address = cursor.fetchall()[0][0]
        # cursor.execute("insert into pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, date_time, type_code, type_name, ip_address, created_on) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [set_pressure, pressure_unit, valve_size, valve_class, tested_by, serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, cur_datetime, test_type, test_type_name ,ip_address, created_on])
        # cursor.execute("insert into temp_pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, date_time, type_code, type_name, ip_address, created_on) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [set_pressure, pressure_unit, valve_size, valve_class, tested_by, serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, cur_datetime, test_type, test_type_name ,ip_address, created_on])
        



        # print("pressure unit: " + pressure_unit)
        # print(f"valve size : {valve_size}")
        # print(f"valve class : {valve_class}")
        # print(f"tested by: {tested_by}")
        # print(f"ip address: {ip_address}")
        # cursor.execute("insert into change_test_tbl values ('123','Arca Airshell',1)")
    return HttpResponse("created")

def hydroshellfunction(request):
    threading.Thread(target=log_handler_execution, args=("hydroshellfunction",)).start()
    global valve_size
    with connection.cursor() as cursor:
        serial_number = select_query("select valve_serial_number from serial_tbl",[],False)[0][0]
        tpa_pa_insert(serial_number, 5)
        # cursor.execute("select * from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Shell'",[serial_number])
        # data = cursor.fetchall()
        # pressure_unit = data[0][19]
        # get_valve_size = data[0][42]
        # print("--------------------------------------------")
        # print(get_valve_size)
        # if (get_valve_size == '25 NB (1")'):
        #     valve_size = 3
        # elif (get_valve_size == '40 NB (1 1/2")'):
        #     valve_size = 4
        # elif (get_valve_size == '50 NB (2")'):
        #     valve_size = 5
        # elif (get_valve_size == '65 NB (2 1/2")'):
        #     valve_size = 6
        # elif (get_valve_size == '15 NB (1/2")'):
        #     valve_size = 1
        
        # get_valve_class = data[0][44]
        # if (get_valve_class == "#150"):
        #     valve_class = 150
        # elif (get_valve_class == "#300"):
        #     valve_class = 300

        # tested_by = "F1636"

        # cursor.execute("update pressure_analysis set status=0 and cycle_complete='0' where status=1 and cycle_complete='1'")

        # test_type = 5
        # test_type_name = "Hydro Shell"
        # set_pressure = data[0][18]
        # set_time_unit = data[0][21]
        # set_time = data[0][20]
        # write_hmi = 0
        # status = 1
        # station_status = 1
        # now = datetime.datetime.now()
        # cur_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        # cal_due_hydro_1 = '0000-00-00 00:00:00'
        # cal_due_hydro_2 = "0000-00-00 00:00:00"
        # cal_due_air_1 = "0000-00-00 00:00:00"
        # cal_due_air_2 = "0000-00-00 00:00:00"
        # cal_due_others_1 = "0000-00-00 00:00:00"
        # cal_due_others_2 = "0000-00-00 00:00:00"
        # cal_due_others_3 = "0000-00-00 00:00:00"
        # cal_done_hydro_1 = "0000-00-00 00:00:00"
        # cal_done_hydro_2 = "0000-00-00 00:00:00"
        # cal_done_air_1 = "0000-00-00 00:00:00"
        # cal_done_air_2 = "0000-00-00 00:00:00"
        # cal_done_others_1 = "0000-00-00 00:00:00"
        # cal_done_others_2 = "0000-00-00 00:00:00"
        # cal_done_others_3 = "0000-00-00 00:00:00"
        # cal_due_wrench = "0000-00-00 00:00:00"
        # created_on = now.strftime("%Y-%m-%d %H:%M:%S")
        # cursor.execute("select hmi_ip_address from configuration_tbl")
        # ip_address = cursor.fetchall()[0][0]
        # cursor.execute("insert into pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, date_time, type_code, type_name, ip_address, created_on) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [set_pressure, pressure_unit, valve_size, valve_class, tested_by, serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, cur_datetime, test_type, test_type_name ,ip_address, created_on])



        # print("pressure unit: " + pressure_unit)
        # print(f"valve size : {valve_size}")
        # print(f"valve class : {valve_class}")
        # print(f"tested by: {tested_by}")
        # print(f"ip address: {ip_address}")
        # cursor.execute("insert into change_test_tbl values ('123','Arca Airshell',1)")
    return HttpResponse("created")

def hydroseatfunction(request):
    threading.Thread(target=log_handler_execution, args=("hydroseatfunction",)).start()
    global valve_size
    with connection.cursor() as cursor:
        serial_number = select_query("select valve_serial_number from serial_tbl",[],False)[0][0]
        tpa_pa_insert(serial_number, 2)
        # cursor.execute("select * from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Seat'",[serial_number])
        # data = cursor.fetchall()
        # pressure_unit = data[0][19]
        # get_valve_size = data[0][42]
        # print("--------------------------------------------")
        # print(get_valve_size)
        # if (get_valve_size == '25 NB (1")'):
        #     valve_size = 3
        # elif (get_valve_size == '40 NB (1 1/2")'):
        #     valve_size = 4
        # elif (get_valve_size == '50 NB (2")'):
        #     valve_size = 5
        # elif (get_valve_size == '65 NB (2 1/2")'):
        #     valve_size = 6
        # elif (get_valve_size == '15 NB (1/2")'):
        #     valve_size = 1
        
        # get_valve_class = data[0][44]
        # if (get_valve_class == "#150"):
        #     valve_class = 150
        # elif (get_valve_class == "#300"):
        #     valve_class = 300

        # tested_by = "F1636"

        # cursor.execute("update pressure_analysis set status=0 and cycle_complete='0' where status=1 and cycle_complete='1'")

        # test_type = 2
        # test_type_name = "Hydro Seat"
        # set_pressure = data[0][18]
        # set_time_unit = data[0][21]
        # set_time = data[0][20]
        # write_hmi = 0
        # status = 1
        # station_status = 1
        # now = datetime.datetime.now()
        # cur_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        # cal_due_hydro_1 = '0000-00-00 00:00:00'
        # cal_due_hydro_2 = "0000-00-00 00:00:00"
        # cal_due_air_1 = "0000-00-00 00:00:00"
        # cal_due_air_2 = "0000-00-00 00:00:00"
        # cal_due_others_1 = "0000-00-00 00:00:00"
        # cal_due_others_2 = "0000-00-00 00:00:00"
        # cal_due_others_3 = "0000-00-00 00:00:00"
        # cal_done_hydro_1 = "0000-00-00 00:00:00"
        # cal_done_hydro_2 = "0000-00-00 00:00:00"
        # cal_done_air_1 = "0000-00-00 00:00:00"
        # cal_done_air_2 = "0000-00-00 00:00:00"
        # cal_done_others_1 = "0000-00-00 00:00:00"
        # cal_done_others_2 = "0000-00-00 00:00:00"
        # cal_done_others_3 = "0000-00-00 00:00:00"
        # cal_due_wrench = "0000-00-00 00:00:00"
        # created_on = now.strftime("%Y-%m-%d %H:%M:%S")
        # cursor.execute("select hmi_ip_address from configuration_tbl")
        # ip_address = cursor.fetchall()[0][0]
        # cursor.execute("insert into pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, date_time, type_code, type_name, ip_address, created_on) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", [set_pressure, pressure_unit, valve_size, valve_class, tested_by, serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, cur_datetime, test_type, test_type_name ,ip_address, created_on])



        # print("pressure unit: " + pressure_unit)
        # print(f"valve size : {valve_size}")
        # print(f"valve class : {valve_class}")
        # print(f"tested by: {tested_by}")
        # print(f"ip address: {ip_address}")
        # cursor.execute("insert into change_test_tbl values ('123','Arca Airshell',1)")
    return HttpResponse("created")


def gettestbuttonstatus(request):
    threading.Thread(target=log_handler_execution, args=("gettestbuttonstatus",)).start()
    with connection.cursor() as cursor:
        row = select_query("select * from pressure_analysis where status = 1",[],False)
    if (len(row) > 0):
        if (row[0][29] == 2 or row[0][29] == 3):
            return HttpResponse(row[0][35] + ":#e85d04")
        elif (row[0][29] == 1):
            return HttpResponse(row[0][35] + ":green")
        else:
            return HttpResponse(row[0][35] + ":red")
    return HttpResponse("error")


def cyclecompletefunctionadmin(request):
    threading.Thread(target=log_handler_execution, args=("cyclecompletefunctionadmin",)).start()
    with connection.cursor() as cursor:
        update_query("update pressure_analysis set status = 0 and cycle_complete = 0")
        update_query("update temp_pressure_analysis set status = 0 and cycle_complete = 0")
        # cursor.execute("update master_ip_address set push_data = 1")
    

    return redirect("admin_dashboardview")

def cyclecompletefunctionr12(request):
    threading.Thread(target=log_handler_execution, args=("cyclecompletefunctionr12",)).start()
    
    try:
        global r12connection
        with connection.cursor() as cursor:
            update_query("update pressure_analysis set status = 0 and cycle_complete = 0")
            # cursor.execute("update master_ip_address set push_data = 1")
        # update_query("update master_temp_data set station_status='inactive' where id=1")
        cellid = select_query("select cell_id from configuration_tbl")[0]["cell_id"]
        serial = select_query("select * from serial_tbl")[0]["valve_serial_number"]
        # attempts = select_query("SELECT type_name, count(*) as attempt FROM qnq.pressure_analysis where valve_serial_number = 'M4A2309900' group by type_name;")
        temp_pa_data = select_query("select * from temp_pressure_analysis")
        
        for row in temp_pa_data:
            serial = row["valve_serial_number"]
            testtype = row["test_type"]
            createdon = row["created_on"]
            typename = row["type_name"]
            setpressure = row["set_pressure"]
            valvestatus = row["valve_status"]
            if (valvestatus == 1):
                testresult = "Pass"
            elif (valvestatus == 0):
                testresult = "Fail"
            else:
                testresult = "Not Tested"
            
            startpressure = row["start_pressure"]/10
            endpressure = row["result_pressure"]/10
            hydraulicpressure = row["hydro_pressure"]/10
            settime = row["set_time"]
            # hydroseatleak = row["hydro_seat_leak"]
            # airshellleak = row["air_shell_leak"]
            # airseatleak = row["air_seat_leak"]
            # bubblecount = row["bubble_count"]
            hydroseatleak = None
            airshellleak = None
            airseatleak = None
            bubblecount = 0
            hydroshellleak = None
            test_rdg_1_title = "Start Pressure"
            test_rdg_2_title = "End Pressure"
            test_rdg_3_title = "Clamping Pressure"
            test_rdg_4_title = "Test Duration"
            test_rdg_5_title = "Seat Leak (Water)"
            test_rdg_6_title = "Shell Leak (Air)"
            test_rdg_7_title = "Seat Leak (Air)"
            test_rdg_8_title = "Bubble Count"
            test_rdg_9_title = "Test Difference"
            test_rdg_1_unit = row["pressure_unit"]
            test_rdg_2_unit = row["pressure_unit"]
            test_rdg_3_unit = row["pressure_unit"]
            test_rdg_4_unit = row["set_time_unit"]
            test_rdg_5_unit = "ml"
            test_rdg_6_unit = "pa/sec"
            test_rdg_7_unit = "nm3/hr"
            test_rdg_9_unit = "Bar G"
            
            reason_for_fail = row["others_1"]
            
            if (bubblecount <= 1):
                test_rdg_8_unit = "bubble"
            elif (bubblecount > 1):
                test_rdg_8_unit = "bubbles"
                
            testedby = select_query("select opr_token from logged_user")[0]["opr_token"]
            
            if (testtype == 1):
                data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Air Shell' and cell_id = %s",[serial, cellid])[0]
                headerid = data["header_id"]
                testid = data["test_id"]
                tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Air Shell'",[serial])[0]
                acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
                airshellleak = row["air_shell_leak"]
            elif (testtype == 4):
                data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Air Seat' and cell_id = %s",[serial, cellid])[0]
                headerid = data["header_id"]
                testid = data["test_id"]
                tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Air Seat'",[serial])[0]
                acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
                airseatleak = row["air_seat_leak"]
            elif (testtype == 5):
                data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Hydro Shell' and cell_id = %s",[serial, cellid])[0]
                headerid = data["header_id"]
                testid = data["test_id"]
                tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Shell'",[serial])[0]
                acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
                hydroshellleak = startpressure - endpressure
            elif (testtype == 2):
                data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Hydro Seat' and cell_id = %s",[serial, cellid])[0]
                headerid = data["header_id"]
                testid = data["test_id"]
                tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Seat'",[serial])[0]
                acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
                hydroseatleak = row["hydro_seat_leak"]
            if endpressure < acceptable_high_limits_result:
                acceptance_criteria = f"{acceptable_high_limits_result} <= {endpressure}"
            else:
                acceptance_criteria = f"{acceptable_high_limits_result} <= {endpressure}"
            attemptno = select_query("select count(*) from pressure_analysis where valve_serial_number = %s and test_type = %s",[serial, testtype],False)[0][0]
            ret = r12connection.execute("insert into sing_ssd.xxfmmfg_scada_test_result_det (cellid, serial_no, attempt_no, creation_date, test_type, acceptance_criteria, test_result, test_rdg_1, test_rdg_2, test_rdg_3, test_rdg_4, test_rdg_5, test_rdg_6, test_rdg_7, test_rdg_8, test_rdg_1_title, test_rdg_2_title, test_rdg_3_title, test_rdg_4_title, test_rdg_5_title, test_rdg_6_title, test_rdg_7_title, test_rdg_8_title, test_rdg_1_unit, test_rdg_2_unit, test_rdg_3_unit, test_rdg_4_unit, test_rdg_5_unit, test_rdg_6_unit, test_rdg_7_unit, test_rdg_8_unit, header_id, test_id, opr_token, pc_category, test_rdg_9, test_rdg_9_title, test_rdg_9_unit, reason_for_fail) values (%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,%s,%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,'%s','%s','%s',%s,'%s','%s','%s')" % (cellid, serial, attemptno, createdon, typename, acceptance_criteria, testresult, startpressure, endpressure, hydraulicpressure, settime, hydroseatleak if hydroseatleak is not None else "null", airshellleak if airshellleak is not None else "null", airseatleak if airseatleak is not None else "null", bubblecount, test_rdg_1_title, test_rdg_2_title, test_rdg_3_title, test_rdg_4_title, test_rdg_5_title, test_rdg_6_title, test_rdg_7_title, test_rdg_8_title, test_rdg_1_unit, test_rdg_2_unit, test_rdg_3_unit, test_rdg_4_unit, test_rdg_5_unit, test_rdg_6_unit, test_rdg_7_unit, test_rdg_8_unit, headerid if headerid is not None else "null", testid, testedby, f"Arca {typename}", hydroshellleak if hydroshellleak is not None else "null", test_rdg_9_title, test_rdg_9_unit, reason_for_fail))
            r12connection.commit()
            
        update_query("truncate table temp_pressure_analysis")
        # create_report()
    except Exception as e:
        threading.Thread(target=log_exception, args=("cyclecompletefunctionr12", type(e).__name__, "Error while completing R12 Cycle", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while completing R12 Cycle : {e}","red"))
        raise e
    return redirect("r12_dashboardview")


def create_report():
    print("creating report")
    product_details = select_query("select product_name, hshell_set_pressure, hshell_set_duration, hseat_set_pressure, hseat_set_duration, ashell_set_pressure, ashell_set_duration, aseat_set_pressure, aseat_set_duration from product where product_name = 'jaga'")
    parameter_details = select_query("select s.valve_serial_number, t.test_name, t.driving_param1_value from serial_tbl s left join testing_parameters_t t on s.valve_serial_number = t.serial_number;")
    update_query("truncate table temp_result_tbl")
    product_details = product_details[0]
    parameter_details = parameter_details
    product = product_details["product_name"]
    serial = parameter_details[0]["valve_serial_number"]
    size = parameter_details[0]["driving_param1_value"]
    
    for type in parameter_details:
        pressure = None
        duration = None
        if (type["test_name"] == "Arca Hydro Shell"):
            pressure = product_details["hshell_set_pressure"]
            duration = product_details["hshell_set_duration"]
        elif (type["test_name"] == "Arca Hydro Seat"):
            pressure = product_details["hseat_set_pressure"]
            duration = product_details["hseat_set_duration"]
        elif (type["test_name"] == "Arca Air Seat"):
            pressure = product_details["aseat_set_pressure"]
            duration = product_details["aseat_set_duration"]
        elif (type["test_name"] == "Arca Air Shell"):
            pressure = product_details["ashell_set_pressure"]
            duration = product_details["ashell_set_duration"]
            
        update_query("insert into temp_result_tbl values (%s,%s,%s,%s,%s,%s)",[product,serial,type["test_name"],size,pressure,duration])
    
    data = select_query("select * from temp_result_tbl")
    convert_json_to_csv(data,"files/report.csv")



def get_pressure_analysis_data(request):
    threading.Thread(target=log_handler_execution, args=("get_pressure_analysis_data",)).start()
    try:
        with connection.cursor() as cursor:
            results = select_query("select tested_by, set_pressure, set_time, pressure, actual_time, start_pressure, valve_status, pressure_unit, set_time_unit, result_pressure from pressure_analysis where status=1")
        return JsonResponse(results[0], safe=False)
    except Exception as e:
        threading.Thread(target=log_exception, args=("get_pressure_analysis_data", type(e).__name__, "Error while getting pressure analysis data", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while getting pressure analysis data : {e}", "red"))
        return JsonResponse(None, safe=False)               

@log
def load_live_status(request):
    threading.Thread(target=log_handler_execution, args=("load_live_status",)).start()
    update_query("truncate table temp_pressure_analysis")
    with connection.cursor() as cursor:
        update_query("update serial_tbl set valve_serial_number = %s", [request.POST.get("sn")])
        update_query("insert into master_serial (valve_serial_no) values (%s)",[request.POST.get("sn")])
    
    data = select_query("select test_name from testing_parameters_t where serial_number = %s", [request.POST.get("sn")], False)
    testing_data = select_query("select * from testing_parameters_t where serial_number = %s", [request.POST.get("sn")], False)
    update_query("truncate table temp_testing_parameters_t")
    for row in testing_data:
        lst = [value for value in row]
        update_query("insert into temp_testing_parameters_t values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", lst)
        
    names = select_query("select test_name from temp_testing_parameters_t where serial_number = %s",[request.POST.get("sn")], False)
    print(colored("written to temp", "green"))
    print(names)
    for name in names:
        if name[0] == "Arca Air Seat":
            result = select_query("select * from temp_testing_parameters_t where serial_number = %s and test_name = %s",[request.POST.get("sn"), name[0]])
            result = result[0]
            write_to_hmi_float(2175,result["ACCEPTABLE_HIGH_LIMITS_RESULT"] * 1000/60)

            print(colored(f"measuring : {int(result['HOLDINGTIME_VALUE'] )}","yellow"))
            write_to_hmi(2155, int(result["HOLDINGTIME_VALUE"] * 10))
            print(colored(f"measuring : {int(result['HOLDINGTIME_VALUE'] * 10)}","yellow"))
            write_to_hmi_float(2160, result["PRESSUREHIGHLIMIT"])
            write_to_hmi_float(2165, result["PRESSUREHIGHLIMIT"])
            write_to_hmi_float(2170, result["PRESSUREHIGHLIMIT"])
            print(colored("Successfully written to hmi float", "green"))

    return redirect("r12_live_status")


def gettestingparameterdata(request):
    threading.Thread(target=log_handler_execution, args=("gettestingparameterdata",)).start()
    try:
        with connection.cursor() as cursor:
            
            result = select_query("select valve_serial_number, type_name from pressure_analysis where status = 1 and cycle_complete = '1'",[],False)[0]
            serial_number = result[0]
            get_test_type_name = result[1]
            test_type_name = f"Arca {get_test_type_name}"
            
            
            data = select_query("select * from temp_testing_parameters_t where serial_number = %s and test_name = %s", [serial_number, test_type_name],False)[0]
        
        jsondata = {
            'cell_id': data[0],
            'header_id': data[2],
            'test_id' : data[4],
            'test_media' : data[6],
            'item_code' : data[7],
            'inv_item_id' : data[8],
            'job_number' : data[10],
            'wip_entity_id' : data[11],
            'actuator_action' : data[48],
            'inv_org' : data[1],
            'model_number' : data[3]
        }

        return JsonResponse(jsondata)
    except Exception as e:
        threading.Thread(target=log_exception, args=("gettestingparameterdata", type(e).__name__, "Error while getting testing parameter data", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while getting testing parameter data : {e}", "red"))
        return JsonResponse({})

def getautomanual(requets):
    threading.Thread(target=log_handler_execution, args=("getautomanual",)).start()
    # with connection.cursor() as cursor:
    #     cursor.execute("select auto_manual from master_ip_address")
    #     data = cursor.fetchall()[0][0]
    data = getstatus(2012)
    # update_query("update master_ip_address set auto_manual = '%s'", [data])
    # with connection.cursor() as c:
    #     c.execute("update master_ip_address set auto_manual = %s",[data])
    
    
    if (data == 1):
        return HttpResponse("Manual")
    
    return HttpResponse("Auto")


def getalarmmessage(request):
    threading.Thread(target=log_handler_execution, args=("getalarmmessage",)).start()
    num = getstatus(2017)
    alarm_name = select_query(f"select alarm_name from alarm_details where alarm_id = '{num}'")
    if (len(alarm_name) > 0):
        data = alarm_name[0]["alarm_name"]
    else:
        data = "Alarm Message"
    return HttpResponse(data)


def updatereporttable(request):
    threading.Thread(target=log_handler_execution, args=("updatereporttable",)).start()
    cellid = select_query("select cell_id from configuration_tbl",[],False)[0][0]
    row = select_query("select * from pressure_analysis where id = %s",[request.POST.get("id")])[0]
    
    serial = row["valve_serial_number"]
    
    
    
    testtype = row["test_type"]
    createdon = row["created_on"]
    typename = row["type_name"]
    setpressure = row["set_pressure"]
    valvestatus = row["valve_status"]
    if (valvestatus == 1):
        testresult = "Pass"
    elif (valvestatus == 0):
        testresult = "Fail"
    else:
        testresult = "Not Tested"
    
    startpressure = row["start_pressure"]/10
    endpressure = row["result_pressure"]/10
    hydraulicpressure = row["hydro_pressure"]/10
    settime = row["set_time"]
    # hydroseatleak = row["hydro_seat_leak"]
    # airshellleak = row["air_shell_leak"]
    # airseatleak = row["air_seat_leak"]
    # bubblecount = row["bubble_count"]
    hydroseatleak = None
    airshellleak = None
    airseatleak = None
    bubblecount = 0
    hydroshellleak = None
    test_rdg_1_title = "Start Pressure"
    test_rdg_2_title = "End Pressure"
    test_rdg_3_title = "Clamping Pressure"
    test_rdg_4_title = "Test Duration"
    test_rdg_5_title = "Seat Leak (Water)"
    test_rdg_6_title = "Shell Leak (Air)"
    test_rdg_7_title = "Seat Leak (Air)"
    test_rdg_8_title = "Bubble Count"
    test_rdg_9_title = "Test Difference"
    test_rdg_1_unit = row["pressure_unit"]
    test_rdg_2_unit = row["pressure_unit"]
    test_rdg_3_unit = row["pressure_unit"]
    test_rdg_4_unit = row["set_time_unit"]
    test_rdg_5_unit = "ml"
    test_rdg_6_unit = "pa/sec"
    test_rdg_7_unit = "nm3/hr"
    test_rdg_9_unit = "Bar G"
    
    reason_for_fail = row["others_1"]
    
    if (bubblecount <= 1):
        test_rdg_8_unit = "bubble"
    elif (bubblecount > 1):
        test_rdg_8_unit = "bubbles"
        
    testedby = select_query("select opr_token from logged_user")[0]["opr_token"]
    
    if (testtype == 1):
        data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Air Shell' and cell_id = %s",[serial, cellid])[0]
        headerid = data["header_id"]
        testid = data["test_id"]
        tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Air Shell'",[serial])[0]
        acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
        airshellleak = row["air_shell_leak"]
    elif (testtype == 4):
        data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Air Seat' and cell_id = %s",[serial, cellid])[0]
        headerid = data["header_id"]
        testid = data["test_id"]
        tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Air Seat'",[serial])[0]
        acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
        airseatleak = row["air_seat_leak"]
    elif (testtype == 5):
        data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Hydro Shell' and cell_id = %s",[serial, cellid])[0]
        headerid = data["header_id"]
        testid = data["test_id"]
        tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Shell'",[serial])[0]
        acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
        hydroshellleak = startpressure - endpressure
    elif (testtype == 2):
        data = select_query("select header_id, test_id from temp_pressure_analysis where valve_serial_number = %s and type_name = 'Hydro Seat' and cell_id = %s",[serial, cellid])[0]
        headerid = data["header_id"]
        testid = data["test_id"]
        tp_data = select_query("select acceptable_high_limits_result from testing_parameters_t where serial_number=%s and test_name='Arca Hydro Seat'",[serial])[0]
        acceptable_high_limits_result = tp_data["acceptable_high_limits_result"]
        hydroseatleak = row["hydro_seat_leak"]
    if endpressure < acceptable_high_limits_result:
        acceptance_criteria = f"{acceptable_high_limits_result} <= {endpressure}"
    else:
        acceptance_criteria = f"{acceptable_high_limits_result} <= {endpressure}"
    attemptno = select_query("select count(*) from pressure_analysis where valve_serial_number = %s and test_type = %s",[serial, testtype],False)[0][0]
    ret = r12connection.execute("insert into sing_ssd.xxfmmfg_scada_test_result_det (cellid, serial_no, attempt_no, creation_date, test_type, acceptance_criteria, test_result, test_rdg_1, test_rdg_2, test_rdg_3, test_rdg_4, test_rdg_5, test_rdg_6, test_rdg_7, test_rdg_8, test_rdg_1_title, test_rdg_2_title, test_rdg_3_title, test_rdg_4_title, test_rdg_5_title, test_rdg_6_title, test_rdg_7_title, test_rdg_8_title, test_rdg_1_unit, test_rdg_2_unit, test_rdg_3_unit, test_rdg_4_unit, test_rdg_5_unit, test_rdg_6_unit, test_rdg_7_unit, test_rdg_8_unit, header_id, test_id, opr_token, pc_category, test_rdg_9, test_rdg_9_title, test_rdg_9_unit, reason_for_fail) values (%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,%s,%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,'%s','%s','%s',%s,'%s','%s','%s')" % (cellid, serial, attemptno, createdon, typename, acceptance_criteria, testresult, startpressure, endpressure, hydraulicpressure, settime, hydroseatleak if hydroseatleak is not None else "null", airshellleak if airshellleak is not None else "null", airseatleak if airseatleak is not None else "null", bubblecount, test_rdg_1_title, test_rdg_2_title, test_rdg_3_title, test_rdg_4_title, test_rdg_5_title, test_rdg_6_title, test_rdg_7_title, test_rdg_8_title, test_rdg_1_unit, test_rdg_2_unit, test_rdg_3_unit, test_rdg_4_unit, test_rdg_5_unit, test_rdg_6_unit, test_rdg_7_unit, test_rdg_8_unit, headerid if headerid is not None else "null", testid, testedby, f"Arca {typename}", hydroshellleak if hydroshellleak is not None else "null", test_rdg_9_title, test_rdg_9_unit, reason_for_fail))
    r12connection.commit()
    # with connection.cursor() as c:
    #     c.execute("truncate table report_tbl")
    #     c.execute("insert into report_tbl values (%s,%s,%s)",[request.POST.get("serial"),1, request.POST.get("test_name")])
    
    return HttpResponse("Inserted to R12 Database")


def getgraphdata(request):
    threading.Thread(target=log_handler_execution, args=("getgraphdata",)).start()
    # data = select_query("select pressure, date_time from current_status where test_type=5 and valve_serial_number='v1729-3' and pressure > 0 limit 60", True)
    return JsonResponse({}, safe=False)


def getstatus(num):
    global tesleadsmartsyncx
    # print(f"getting value from hmi : {num}")
    return tesleadsmartsyncx.read_holding_registers(num, 1).registers[0]

def getactionbuttonstatus(request):
    threading.Thread(target=log_handler_execution, args=("getactionbuttonstatus",)).start()
    # print("getactionbuttonstatus")
    # data = select_query("select * from live_status", True)
    # return JsonResponse(data, safe=False)
    data = [{"clamping_status": getstatus(2300), 
             "prefilling_status": getstatus(2301), 
             "booster_status": getstatus(2302), 
             "pressurizing_status": getstatus(2303), 
             "timer_status": getstatus(2304), 
             "declamping_status": getstatus(2306), 
             "door_status": getstatus(2307), 
             "cycle_status": getstatus(2309), 
             "vacuum_status": getstatus(2311), 
             "vent_status": getstatus(2310), 
             "air_status": getstatus(2312), 
             "pressure_drain_status": getstatus(2305), 
             "emergency_stop_status": getstatus(2313),
             "pressure" : getstatus(2008),
             "actual_time" : getstatus(2006),
             "air_shell_leak": read_from_hmi_float(2120),
             "air_seat_leak": read_from_hmi_float(2125),
             "hydro_shell_leak": read_from_hmi_float(2130),
             "hydro_seat_leak": read_from_hmi_float(2135),
             "bubble_count": getstatus(2124)}]
    return JsonResponse(data,safe=False)


def updataconfigdata(request):
    threading.Thread(target=log_handler_execution, args=("updataconfigdata",)).start()
    address = request.POST.get("address")
    port = request.POST.get("port")
    database = request.POST.get("database")
    option = request.POST.get("option")
    username = request.POST.get("username")
    password = request.POST.get("password")
    hmiipaddress = request.POST.get("hmiipaddress")
    hmiport = request.POST.get("hmiport")
    goodresult = request.POST.get("goodresult")
    badresult = request.POST.get("badresult")
    cellid = request.POST.get("cellid")
    r12connection = 0
    alarmsystem = 0
    hmiconnection = 0
    for item in request.POST.getlist("connection"):
        if (item == "r12connection"):
            r12connection = 1
        elif (item == "alarmsystem"):
            alarmsystem = 1
        elif (item == "hmiconnection"):
            hmiconnection = 1
    # print(address)
    # print(port)
    # print(database)
    # print(option)
    # print(username)
    # print(password)
    # print(hmiipaddress)
    # print(hmiport)
    # print(goodresult)
    # print(badresult)
    # print(cellid)
    # print(r12connection)
    # print(alarmsystem)
    # print(hmiconnection)
    with connection.cursor() as c:
        update_query("truncate table configuration_tbl")
        update_query("insert into configuration_tbl values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s','%s','%s')",[address, port, database, option, username, password, hmiipaddress, hmiport, cellid, goodresult, badresult, r12connection, alarmsystem, hmiconnection])
    return redirect("admin_configuration")
    

def getconfigbadresult(request):
    threading.Thread(target=log_handler_execution, args=("getconfigbadresult",)).start()
    data = select_query("select bad_result from configuration_tbl",[], False)
    return HttpResponse(data[0][0])

def getconfiggoodresult(request):
    threading.Thread(target=log_handler_execution, args=("getconfiggoodresult",)).start()
    data = select_query("select good_result from configuration_tbl",[], False)
    return HttpResponse(data[0][0])

def convert_json_to_csv(data, filepath):
    df = pd.DataFrame(data)

    # Save DataFrame to CSV
    df.to_csv(filepath, index=False)
    os.startfile("files\\report.csv")


def getproductbyid(request):
    threading.Thread(target=log_handler_execution, args=("getproductbyid",)).start()
    data = select_query(f"select id, product_id,product_name,product_description, size, class, type, hshell_set_pressure, hshell_set_holding_time, hshell_set_duration, hseat_set_pressure, hseat_set_holding_time, hseat_set_duration, ashell_set_pressure, ashell_set_holding_time, ashell_set_duration,aseat_set_pressure, aseat_set_holding_time, aseat_set_duration, flanged_type, actuator_type from product where id = {request.POST.get('id')}")
    return JsonResponse(data,safe=False)


def temptest(request):
    threading.Thread(target=log_handler_execution, args=("temptest",)).start()
    data = select_query("select * from product")
    return JsonResponse(data,safe=False)

@log
def admin_test_serial(request):
    threading.Thread(target=log_handler_execution, args=("admin_test_serial",)).start()
    with connection.cursor() as cursor:
        update_query("update pressure_analysis set status = 0 and cycle_complete = '0'")
        update_query("update temp_pressure_analysis set status = 0 and cycle_complete = '0'")
    with connection.cursor() as cursor:
        
        data = select_query("select cell_id from configuration_tbl",[],False)
    products = select_query("select id, product_name from product",[])
    return render(request, "Admin_Test_Serial.html",{'cell_id': data[0][0], 'products':products})


def checkautotestchange(request):
    threading.Thread(target=log_handler_execution, args=("checkautotestchange",)).start()
    serial = select_query("select * from serial_tbl")[0]
    auto_test_change = getstatus(2114)
    auto_manual = getstatus(2012)
    if (auto_manual == 0):
        if (auto_test_change == 1):
            tpa_pa_insert(serial["valve_serial_number"],getstatus(2115))
    
    return HttpResponse("done")




def tpa_pa_insert(serial, test_type):
    
    if (test_type == 1):
        arca_test_name = "Arca Air Shell"
        test_name = "Air Shell"
    elif (test_type == 4):
        arca_test_name = "Arca Air Seat"
        test_name = "Air Seat"
    elif (test_type == 5):
        arca_test_name = "Arca Hydro Shell"
        test_name = "Hydro Shell"
    elif (test_type == 2):
        arca_test_name = "Arca Hydro Seat"
        test_name = "Hydro Seat"
        
    data = select_query("select * from temp_testing_parameters_t where serial_number = %s and test_name = %s",[serial, arca_test_name])[0]
    valvesize = convert_value_size_to_int(data["DRIVING_PARAM1_VALUE"])
    user = select_query("select opr_token from logged_user")[0]
    ip = select_query("select hmi_ip_address from configuration_tbl")[0]["hmi_ip_address"]
    update_query("update pressure_analysis set status = '0' and cycle_complete = '0' where status = '1' and cycle_complete ='1'")
    update_query("update temp_pressure_analysis set status = '0' and cycle_complete = '0' where status = '1' and cycle_complete ='1'")
    cellid = data["CELL_ID"]
    headerid = data["HEADER_ID"]
    test_id = data["TEST_ID"]
    update_query("insert into pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_Serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, type_code, type_name,ip_address,created_on, cell_id, header_id, test_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",[data["PRESSUREHIGHLIMIT"], data["PRESSURE_UOM"], valvesize, int(data["DRIVING_PARAM2_VALUE"][1:]), user["opr_token"], serial, data["HOLDINGTIME_UOM"], data["HOLDINGTIME_VALUE"], test_type, 0, 1, 1, test_type, test_name, ip, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),cellid, headerid, test_id])
    
    update_query("insert into temp_pressure_analysis (set_pressure, pressure_unit, valve_size, valve_class, tested_by, valve_Serial_number, set_time_unit, set_time, test_type, write_hmi, status, station_status, type_code, type_name,ip_address,created_on, cell_id, header_id, test_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",[data["PRESSUREHIGHLIMIT"], data["PRESSURE_UOM"], valvesize, int(data["DRIVING_PARAM2_VALUE"][1:]), user["opr_token"], serial, data["HOLDINGTIME_UOM"], data["HOLDINGTIME_VALUE"], test_type, 0, 1, 1, test_type, test_name, ip, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),cellid, headerid, test_id])
    
    write_to_hmi(2114,0)
    
    write_to_hmi(2000, int(data["PRESSUREHIGHLIMIT"]))
    
    write_to_hmi(2001, valvesize)
    write_to_hmi(2002, int(data["DRIVING_PARAM2_VALUE"][1:]))
    write_to_hmi(2003, int(data["HOLDINGTIME_VALUE"]))
    write_to_hmi(2004, test_type)
    write_to_hmi(2101,1)
    write_to_hmi(2102,1)
    write_to_hmi(2103,1)
    write_to_hmi(2104,1)
    write_to_hmi(2105,1)
    

def write_to_hmi_float( address, float_value):
    global tesleadsmartsyncx
    # Convert the float to bytes using struct
    float_bytes = struct.pack('<f', float_value)  # Big-endian format
    # Split the bytes into two 16-bit integers
    high_word = int.from_bytes(float_bytes[0:2], byteorder='little')
    low_word = int.from_bytes(float_bytes[2:4], byteorder='little')
    
    # Write the high and low words to the holding registers
    tesleadsmartsyncx.write_register(address, high_word)
    tesleadsmartsyncx.write_register(address + 1, low_word)
    
    
# def write_to_hmi_float(add, val):
#     global tesleadsmartsyncx
#     packed_value = struct.pack('>d', val)  # Big-endian float
#     unpacked_value = struct.unpack('>HHHH', packed_value)
#     tesleadsmartsyncx.write_registers(add+1,unpacked_value)
    

def read_from_hmi_float(add):
    global tesleadsmartsyncx
    # Read 2 registers starting from the specified address
    result = tesleadsmartsyncx.read_holding_registers(address=add, count=2)
    if result.isError() or not hasattr(result, "registers"):
        print("Error reading registers")
        return
    
    # Combine the registers into a 32-bit little-endian float
    registers = result.registers
    packed_value = struct.pack('<HH', *registers)  # Combine registers (little-endian)
    floating_value = struct.unpack('<f', packed_value)[0]  # Convert to float (little-endian)
    floating_value = round(floating_value, 5)  # Round to 5 decimal places
    print(floating_value)
    return floating_value


def write_to_hmi(place, value):
    
    global tesleadsmartsyncx
    tesleadsmartsyncx.write_register(place, value)


def convert_value_size_to_int(size):
    valve_size = None
    if (size == '15 NB (1/2")'):
        valve_size = 1
    elif (size == '25 NB (1")'):
        valve_size = 3
    elif (size == '40 NB (1 1/2")'):
        valve_size = 4
    elif (size == '50 NB (2")'):
        valve_size = 5
    elif (size == '65 NB (2 1/2")'):
        valve_size = 6
        
    return valve_size



def convert_flanged_to_int(flanged):
    if (flanged == "FLANGED-RF"):
        return 0
    elif (flanged == "SOCKET WELD END"):
        return 1
    else:
        return 2

    
def convert_actuator_to_int(actuator):
    if (actuator == "AIR TO OPEN"):
        return 0
    elif (actuator == "AIR TO CLOSE"):
        return 1
    
    
    
def getsizeclass(request):
    threading.Thread(target=log_handler_execution, args=("getsizeclass",)).start()
    try:
        serial = request.POST.get("serial")
        data = select_query("select driving_param1_value, driving_param2_value, driving_param3_value, driving_param4_value from testing_parameters_t where serial_number = %s",[serial])
        if (len(data) > 0):
            size = data[0]["driving_param1_value"]
            clas = data[0]["driving_param2_value"]
            flanged_type = data[0]["driving_param3_value"]
            actuator_type = data[0]["driving_param4_value"]
            write_to_hmi(2116,convert_flanged_to_int(flanged_type))
            write_to_hmi(2001,convert_value_size_to_int(size))
            write_to_hmi(2002,int(clas[1:]))
            write_to_hmi(2113, convert_actuator_to_int(actuator_type))
            return HttpResponse(f"Size : {size} Class : {clas}")
        else:
            error = "No serial number found"
            return HttpResponse(error)
    except Exception as e:
        threading.Thread(target=log_exception, args=("getsizeclass", type(e).__name__, "Error while getting product size and class", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while getting product size and class : {e}"))
        err = "Size not found"
        return HttpResponse(err)
    
def getactualpressuretime(request):
    threading.Thread(target=log_handler_execution, args=("getactualpressuretime",)).start()
    data = {
        "pressure" : getstatus(2008),
        "actual_time" : getstatus(2006),
        "air_shell_leak": getstatus(2120),
        "air_seat_leak": getstatus(2121),
        "hydro_shell_leak": getstatus(2122),
        "hydro_seat_leak": getstatus(2123),
        "bubble_count": getstatus(2124)
    }
    
    # update_query("update pressure_analysis set pressure = %s, actual_time = %s, air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s, bubble_count = %s where status = '1'",[data["pressure"], data["actual_time"], data["air_shell_leak"], data["air_seat_leak"], data["hydro_shell_leak"], data["hydro_seat_leak"], data["bubble_count"]])
    # update_query("update temp_pressure_analysis set pressure = %s, actual_time = %s, air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s, bubble_count = %s where status = '1'",[data["pressure"], data["actual_time"], data["air_shell_leak"], data["air_seat_leak"], data["hydro_shell_leak"], data["hydro_seat_leak"], data["bubble_count"]])
    
    return JsonResponse(data, safe=False)


def loopevent(request):
    threading.Thread(target=log_handler_execution, args=("loopevent",)).start()
    valve_status = getstatus(2011)
    result_pressure = getstatus(2013)
    start_pressure = getstatus(2117)
    hydro_pressure = getstatus(2050)
    air_shell_leak = getstatus(2120)
    air_seat_leak = getstatus(2121)
    hydro_shell_leak = getstatus(2122)
    hydro_seat_leak = getstatus(2123)
    
    update_query("update pressure_analysis set hydro_pressure = %s, start_pressure = %s, result_pressure = %s, valve_status = %s, date_time = NOW(), air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s where status = '1'", [hydro_pressure, start_pressure, result_pressure, valve_status, air_shell_leak, air_seat_leak, hydro_shell_leak, hydro_seat_leak])
    update_query("update temp_pressure_analysis set hydro_pressure = %s, start_pressure = %s, result_pressure = %s, valve_status = %s, date_time = NOW(), air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s where status = '1'", [hydro_pressure, start_pressure, result_pressure, valve_status, air_shell_leak, air_seat_leak, hydro_shell_leak, hydro_seat_leak])
    update_query("insert into current_status (sales_order_no,sales_item_no,valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type) SELECT sales_order_no,sales_item_no, valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type FROM pressure_analysis WHERE STATUS='1'")
    
    return HttpResponse("done")


def getproductsizeclass(request):
    threading.Thread(target=log_handler_execution, args=("getproductsizeclass",)).start()
    product_id = request.POST.get("pro")
    sizeclass = select_query("select * from product where id = %s",[product_id])
    return JsonResponse(sizeclass[0],safe=False)

def getavailabletests(request):
    threading.Thread(target=log_handler_execution, args=("getavailabletests",)).start()
    serial = request.POST.get("serial")
    data = select_query("select test_name from temp_testing_parameters_t where serial_number = %s",[serial],False)
    tests = ""
    for test in data:
        tests += test[0]
        tests += "-"
    tests = tests[0:-1]
    return HttpResponse(tests)





def live_status_loop(request):
    print("live status loop before thread")
    threading.Thread(target=log_handler_execution, args=("live_status_loop",)).start()
    print("live status loop after thread")
    #checkautotestchange -> http response (done)
    serial = select_query("select * from serial_tbl")[0]
    auto_test_change = getstatus(2114)
    auto_manual = getstatus(2012)
    if (auto_manual == 0):
        if (auto_test_change == 1):
            tpa_pa_insert(serial["valve_serial_number"],getstatus(2115))
    
    #gettestbuttonstatus
    row = select_query("select * from pressure_analysis where status = 1",[],False)
    if (len(row) > 0):
        if (row[0][29] == 2 or row[0][29] == 3):
            testbuttonstatus = row[0][35] + ":#e85d04"
        elif (row[0][29] == 1):
            testbuttonstatus = row[0][35] + ":green"
        else:
            testbuttonstatus = row[0][35] + ":red"
    else:
        testbuttonstatus = "error"
    
    
    #get_pressure_analysis_data
    try:
        with connection.cursor() as cursor:
            results = select_query("select tested_by, set_pressure, set_time, pressure, actual_time, start_pressure, valve_status, pressure_unit, set_time_unit, result_pressure from pressure_analysis where status=1")
        pressureanalysisdata = results[0]
        if pressureanalysisdata["valve_status"] == 0:
            pressureanalysisdata["goodbadresult"] = select_query("select bad_result from configuration_tbl",[],False)[0][0]
        elif pressureanalysisdata["valve_status"] == 1:
            pressureanalysisdata["goodbadresult"] = select_query("select good_result from configuration_tbl",[],False)[0][0]
        else:
            pressureanalysisdata["goodbadresult"] = ""
    except Exception as e:
        threading.Thread(target=log_exception, args=("get_pressure_analysis_data", type(e).__name__, "Error while getting pressure analysis data", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while getting pressure analysis data : {e}", "red"))
        pressureanalysisdata = None              
    
    
    
    #automanual
    automanualint = getstatus(2012)
    if (automanualint == 1):
        automanual = "Manual"
    else:
        automanual = "Auto"
        
    
    #getalarmmessage
    num = getstatus(2017)
    alarm_name = select_query(f"select alarm_name from alarm_details where alarm_id = '{num}'")
    if (len(alarm_name) > 0):
        alarmmessage = alarm_name[0]["alarm_name"]
    else:
        alarmmessage = "Alarm Message"
        
        
    #testingparameterdata
    try:
        with connection.cursor() as cursor:
            result = select_query("select valve_serial_number, type_name from pressure_analysis where status = 1 and cycle_complete = '1'",[],False)[0]
            serial_number = result[0]
            get_test_type_name = result[1]
            test_type_name = f"Arca {get_test_type_name}"
            data = select_query("select * from temp_testing_parameters_t where serial_number = %s and test_name = %s", [serial_number, test_type_name],False)[0]
        testparameterdata = {
            'cell_id': data[0],
            'header_id': data[2],
            'test_id' : data[4],
            'test_media' : data[6],
            'item_code' : data[7],
            'inv_item_id' : data[8],
            'job_number' : data[10],
            'wip_entity_id' : data[11],
            'actuator_action' : data[48],
            'inv_org' : data[1],
            'model_number' : data[3]
        }
    except Exception as e:
        threading.Thread(target=log_exception, args=("gettestingparameterdata", type(e).__name__, "Error while getting testing parameter data", e)).start()
        print(colored(f"[Error] : [{type(e).__name__}] : Error while getting testing parameter data : {e}", "red"))
        testparameterdata = None
    
    #loopevent
    valve_status = getstatus(2011)
    result_pressure = getstatus(2013)
    start_pressure = getstatus(2117)
    hydro_pressure = getstatus(2050)
    air_shell_leak = read_from_hmi_float(2120)
    air_seat_leak = read_from_hmi_float(2125)
    hydro_shell_leak = read_from_hmi_float(2130)
    hydro_seat_leak = read_from_hmi_float(2135)
    
    update_query("update pressure_analysis set hydro_pressure = %s, start_pressure = %s, result_pressure = %s, valve_status = %s, date_time = NOW(), air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s where status = '1'", [hydro_pressure, start_pressure, result_pressure, valve_status, air_shell_leak, air_seat_leak, hydro_shell_leak, hydro_seat_leak])
    update_query("update temp_pressure_analysis set hydro_pressure = %s, start_pressure = %s, result_pressure = %s, valve_status = %s, date_time = NOW(), air_shell_leak = %s, air_seat_leak = %s, hydro_shell_leak = %s, hydro_seat_leak = %s where status = '1'", [hydro_pressure, start_pressure, result_pressure, valve_status, air_shell_leak, air_seat_leak, hydro_shell_leak, hydro_seat_leak])
    update_query("insert into current_status (sales_order_no,sales_item_no,valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type) SELECT sales_order_no,sales_item_no, valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type FROM pressure_analysis WHERE STATUS='1'")
    
    #actionbuttonstatus
    print("running action button status function")
    actionbuttonstatus = [{"clamping_status": getstatus(2300), 
             "prefilling_status": getstatus(2301), 
             "booster_status": getstatus(2302), 
             "pressurizing_status": getstatus(2303), 
             "timer_status": getstatus(2304), 
             "declamping_status": getstatus(2306), 
             "door_status": getstatus(2307), 
             "cycle_status": getstatus(2309), 
             "vacuum_status": getstatus(2311), 
             "vent_status": getstatus(2310), 
             "air_status": getstatus(2312), 
             "pressure_drain_status": getstatus(2305), 
             "emergency_stop_status": getstatus(2313),
             "pressure" : getstatus(2008),
             "actual_time" : getstatus(2006),
             "air_shell_leak": read_from_hmi_float(2120),
             "air_seat_leak": read_from_hmi_float(2125),
             "hydro_shell_leak": read_from_hmi_float(2130),
             "hydro_seat_leak": read_from_hmi_float(2135),
             "bubble_count": getstatus(2140)}]
    
    response = {
        'gettestbuttonstatus': testbuttonstatus,
        'pressureanalysisdata': pressureanalysisdata,
        'automanual': automanual,
        'alarmmessage': alarmmessage,
        'testparameterdata': testparameterdata,
        'actionbuttonstatus': actionbuttonstatus
    }
    
    return JsonResponse(response, safe=False)


def logout(request):
    update_query("truncate table logged_user")
    
    
def transferreasons(request):
    airshell = request.POST.get("Airshell")
    airseat = request.POST.get("Airseat")
    hydroshell = request.POST.get("Hydroshell")
    hydroseat = request.POST.get("Hydroseat")
    
    print(airshell)
    print(airseat)
    print(hydroshell)
    print(hydroseat)
    
    if airshell is not None:
        update_query("update temp_pressure_analysis set others_1 = %s where type_name = 'Air Shell'", [airshell])
    if airseat is not None:
        update_query("update temp_pressure_analysis set others_1 = %s where type_name = 'Air Seat'", [airseat])
    if hydroshell is not None:
        update_query("update temp_pressure_analysis set others_1 = %s where type_name = 'Hydro Shell'", [hydroshell])
    if hydroseat is not None:
        update_query("update temp_pressure_analysis set others_1 = %s where type_name = 'Hydro Seat'", [hydroseat])
    
    return HttpResponse("done")


def transferreasonsadmin(request):
    airshell = request.POST.get("Airshell")
    airseat = request.POST.get("Airseat")
    hydroshell = request.POST.get("Hydroshell")
    hydroseat = request.POST.get("Hydroseat")
    
    print(airshell)
    print(airseat)
    print(hydroshell)
    print(hydroseat)
    
    if airshell is not None:
        update_query("update pressure_analysis set others_1 = %s where id = (select id from (select max(id) as id from pressure_analysis where type_name = 'Air Shell') as temp)", [airshell])
    if airseat is not None:
        update_query("update pressure_analysis set others_1 = %s where id = (select id from (select max(id) as id from pressure_analysis where type_name = 'Air Seat') as temp)", [airseat])
    if hydroshell is not None:
        update_query("update pressure_analysis set others_1 = %s where id = (select id from (select max(id) as id from pressure_analysis where type_name = 'Hydro Shell') as temp)", [hydroshell])
    if hydroseat is not None:
        update_query("update pressure_analysis set others_1 = %s where id = (select id from (select max(id) as id from pressure_analysis where type_name = 'Hydro Seat') as temp)", [hydroseat])
    
    return HttpResponse("done")



def getallreasons(request):
    reasons = select_query("select reason from reasons")
    return JsonResponse(reasons, safe=False)

def addreason(request):
    reason = request.POST.get("reason")
    update_query("insert into reasons (reason) values (%s)", [reason])
    
    return HttpResponse("done")