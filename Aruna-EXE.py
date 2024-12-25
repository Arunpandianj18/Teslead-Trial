# Aruna Alloys machine EXE
from tkinter import messagebox
import psutil
import os
import pyodbc
import datetime
from pymodbus.client import ModbusTcpClient
import win32com.client
import time
import webbrowser
import tkinter as tk
from PIL import Image, ImageTk
import threading

local_drive_path = "D"
local_database_path = local_drive_path + ":/TesleadSmartSyncX/Database"
local_reports_path = local_drive_path + ":/TesleadSmartSyncX/Reports"
local_excel_pdf_path = local_drive_path + ":/TesleadSmartSyncX/Excel-PDF_reports"
mysql_db_path = "E:\\xampp\\mysql\\bin"
core_database1 = "qnq"
core_database2 = "qnq_completed"

teslead_db = None
TesleadSmartSyncX = None
wait_flag = None
u0024saPDF = None
u0024saOnce = 1
u0024saWait = 1

def kill_taskbar_app(application):
    for proc in psutil.process_iter(['pid', 'name']):
        if application.lower() in proc.info['name'].lower():
            try:
                proc.terminate()
            except psutil.Error:
                print(f"Error killing {application}")
application = "chrome"
kill_taskbar_app(application)

def clear_cache():
    global teslead_db
    try:
        teslead_db.execute("FLUSH QUERY CACHE")
    except Exception as e:
        print(f'Error clear cache : {e}')
        local_db()
        clear_cache()

def initial_msg(title, message):
    response = messagebox.askokcancel(title, message)
    if not response:
        kill_taskbar_app("TesleadSmartSyncX")
initial_msg("Teslead", "Welcome to TesleadSmartSyncX. Ready to begin.")

if not os.path.exists(local_database_path):
    os.makedirs(local_database_path)
if not os.path.exists(local_reports_path):
    os.makedirs(local_reports_path)
if not os.path.exists(local_excel_pdf_path):
    os.makedirs(local_excel_pdf_path)

def local_db():
    global teslead_db
    teslead_X = "DRIVER={MySQL ODBC 9.0 ANSI Driver};Server=localhost;Port=3306;Database=qnq;Uid=root;Password=;OPTION=3;"
    plaster = pyodbc.connect(teslead_X)
    try:
        teslead_db = plaster.cursor()
    except Exception as e:
        print(f'Database Error : {e}')
        local_db()
local_db()

current_date = datetime.date.today()
month_year = current_date.strftime("%m%Y")
current_status = f"current_status_{month_year}"
master_actuator = f"master_actuator_{month_year}"
pressure_analysis = f"pressure_analysis_{month_year}"
teslead_db.execute("CREATE TABLE IF NOT EXISTS qnq_completed." + current_status + " (`id` INT(11) NOT NULL ,`sales_order_no` VARCHAR(50) NOT NULL DEFAULT '',`sales_item_no` VARCHAR(50) NOT NULL DEFAULT '',`valve_serial_number` VARCHAR(50) NOT NULL DEFAULT '123',`pressure` DOUBLE(18,2) NOT NULL DEFAULT '0.00',`hydro_pressure` DOUBLE(18,2) NOT NULL DEFAULT '0.00',`date_time` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',`start_graph` int(11) NOT NULL DEFAULT '1',`test_type` INT(11) NOT NULL DEFAULT '3',`created_on` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,`type_code` int(11) NOT NULL DEFAULT '0',`type_name` VARCHAR(50) NOT NULL DEFAULT '',`pressure_range` INT(11) NOT NULL DEFAULT '0',`cycle_complete` ENUM('0','1') NOT NULL DEFAULT '1') ENGINE=INNODB DEFAULT CHARSET=latin1")
teslead_db.commit()
teslead_db.execute("CREATE TABLE IF NOT EXISTS qnq_completed." + pressure_analysis + " (`id` int(11) NOT NULL, `set_pressure` double(18,3) NOT NULL DEFAULT '0.000', `temprature` double(18,3) NOT NULL DEFAULT '0.000', `max_pressure` double(18,3) NOT NULL DEFAULT '0.000', `pressure_unit` varchar(10) NOT NULL DEFAULT '', `pressure` double(18,3) NOT NULL DEFAULT '0.000', `hydro_pressure` double(18,2) NOT NULL DEFAULT '0.00', `result_pressure` double(18,3) NOT NULL DEFAULT '0.000', `gauge_drop` double(18,3) NOT NULL DEFAULT '0.000', `cavity_connector_l` double(18,3) NOT NULL DEFAULT '0.000', `cavity_connector_r` double(18,3) NOT NULL DEFAULT '0.000', `torque` varchar(50) NOT NULL DEFAULT '', `valve_size` varchar(50) NOT NULL DEFAULT '', `valve_type` varchar(50) NOT NULL DEFAULT '', `valve_class` varchar(50) NOT NULL DEFAULT '', `tested_by` varchar(50) NOT NULL DEFAULT '', `approved_by` varchar(50) NOT NULL DEFAULT '', `valve_tag_no` varchar(50) NOT NULL DEFAULT '', `valve_serial_number` varchar(50) NOT NULL DEFAULT '0', `set_time_unit` varchar(50) NOT NULL DEFAULT '', `set_time` int(11) NOT NULL DEFAULT '0', `actual_time` int(11) NOT NULL DEFAULT '0', `test_type` int(11) NOT NULL DEFAULT '0', `write_hmi` int(1) NOT NULL DEFAULT '1', `start` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', `end` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', `cycle_start` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', `cycle_end` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', `valve_status` int(11) NOT NULL DEFAULT '3', `status` int(11) NOT NULL DEFAULT '0', `date_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `start_graph` int(11) NOT NULL DEFAULT '0', `type_code` int(11) NOT NULL DEFAULT '0', `type_name` varchar(50) NOT NULL DEFAULT '', `pressure_range` int(11) NOT NULL DEFAULT '0', `shell_material` int(11) NOT NULL DEFAULT '0', `sales_order_no` varchar(50) NOT NULL DEFAULT '', `sales_item_no` varchar(50) NOT NULL DEFAULT '', `gad_no` varchar(50) NOT NULL DEFAULT '', `stem_orientation` varchar(50) NOT NULL DEFAULT '', `gear_actuator` varchar(50) NOT NULL DEFAULT '', `ma_gear_ratio` varchar(50) NOT NULL DEFAULT '', `ga_drg_no` varchar(50) NOT NULL DEFAULT '', `appilicability` varchar(50) NOT NULL DEFAULT '', `body_heat` varchar(50) NOT NULL DEFAULT '', `body_mp` varchar(50) NOT NULL DEFAULT '', `body_rt` varchar(50) NOT NULL DEFAULT '', `bonnet_heat` varchar(50) NOT NULL DEFAULT '', `bonnet_mp` varchar(50) NOT NULL DEFAULT '', `bonnet_rt` varchar(50) NOT NULL DEFAULT '', `extn_heat` varchar(50) NOT NULL DEFAULT '', `extn_mp` varchar(50) NOT NULL DEFAULT '', `extn_rt` varchar(50) NOT NULL DEFAULT '', `hydro_1` varchar(50) NOT NULL DEFAULT '', `hydro_2` varchar(50) NOT NULL DEFAULT '', `air_1` varchar(50) NOT NULL DEFAULT '', `air_2` varchar(50) NOT NULL DEFAULT '', `others_1` varchar(50) NOT NULL DEFAULT '', `others_2` varchar(50) NOT NULL DEFAULT '', `others_3` varchar(50) NOT NULL DEFAULT '', `cal_due_hydro_1` datetime NOT NULL, `cal_due_hydro_2` datetime NOT NULL, `cal_due_air_1` datetime NOT NULL, `cal_due_air_2` datetime NOT NULL, `cal_due_others_1` datetime NOT NULL, `cal_due_others_2` datetime NOT NULL, `cal_due_others_3` datetime NOT NULL, `ep_success` enum('0','1') NOT NULL DEFAULT '1', `send_status` enum('yes','no') NOT NULL DEFAULT 'no', `cycle_complete` enum('0','1') NOT NULL DEFAULT '1', `ip_address` varchar(50) NOT NULL DEFAULT '', `report_no` varchar(50) NOT NULL DEFAULT '', `wrench` varchar(50) NOT NULL DEFAULT '', `ball_disc_heat` varchar(50) NOT NULL DEFAULT '', `ball_disc_mp` varchar(50) NOT NULL DEFAULT '', `ball_disc_rt` varchar(50) NOT NULL DEFAULT '', `standard_id` int(11) NOT NULL, `range_hydro_1` varchar(50) NOT NULL DEFAULT '', `range_hydro_2` varchar(50) NOT NULL DEFAULT '', `range_air_1` varchar(50) NOT NULL DEFAULT '', `range_air_2` varchar(50) NOT NULL DEFAULT '', `range_others_1` varchar(50) NOT NULL DEFAULT '', `range_others_2` varchar(50) NOT NULL DEFAULT '', `range_others_3` varchar(50) NOT NULL DEFAULT '', `cal_done_hydro_1` datetime NOT NULL, `cal_done_hydro_2` datetime NOT NULL, `cal_done_air_1` datetime NOT NULL, `cal_done_air_2` datetime NOT NULL, `cal_done_others_1` datetime NOT NULL, `cal_done_others_2` datetime NOT NULL, `cal_done_others_3` datetime NOT NULL, `range_wrench` varchar(50) NOT NULL DEFAULT '', `cal_due_wrench` datetime NOT NULL, `torque_value` varchar(50) NOT NULL DEFAULT '') ENGINE=InnoDB DEFAULT CHARSET=latin1;")
teslead_db.commit()
teslead_db.execute("CREATE TABLE IF NOT EXISTS qnq_completed." + master_actuator + " (`id` INT(11) NOT NULL ,`valve_serial_no` VARCHAR(50) NOT NULL DEFAULT '',`actuator_model_main` VARCHAR(50) NOT NULL DEFAULT '',`actuator_model_by_pass1` VARCHAR(50) NOT NULL DEFAULT '',`actuator_model_by_pass2` VARCHAR(50) NOT NULL DEFAULT '',`wiring_diagram_main` VARCHAR(50) NOT NULL DEFAULT '',`wiring_diagram_by_pass1` VARCHAR(50) NOT NULL DEFAULT '',`wiring_diagram_by_pass2` VARCHAR(50) NOT NULL DEFAULT '',`rpm_value_main` VARCHAR(50) NOT NULL DEFAULT '',`rpm_value_by_pass1` VARCHAR(50) NOT NULL DEFAULT '',`rpm_value_by_pass2` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_open_to_close_main` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_open_to_close_by_pass1` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_open_to_close_by_pass2` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_close_to_open_by_main` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_close_to_open_by_pass1` VARCHAR(50) NOT NULL DEFAULT '',`oper_time_close_to_open_by_pass2` VARCHAR(50) NOT NULL DEFAULT '',`act_s_no` VARCHAR(50) NOT NULL DEFAULT '',`torque_setting` VARCHAR(50) NOT NULL DEFAULT '',`bye_pass_valve_sl_no` VARCHAR(50) NOT NULL DEFAULT '',`closing` VARCHAR(50) NOT NULL DEFAULT '',`break_open` VARCHAR(50) NOT NULL DEFAULT '',`eye_bolt_torque` VARCHAR(50) NOT NULL DEFAULT '',`valve_drying` VARCHAR(50) NOT NULL DEFAULT '',`result_drying` VARCHAR(50) NOT NULL DEFAULT '',`remarks` VARCHAR(300) NOT NULL DEFAULT '',`shift` VARCHAR(50) NOT NULL DEFAULT '',`breakaway` varchar(50) NOT NULL DEFAULT '',`media_drained` varchar(50) NOT NULL DEFAULT '',`vent_bleeder` varchar(50) NOT NULL DEFAULT '',`torque_break_nm` varchar(50) NOT NULL DEFAULT '',`torque_run` varchar(50) NOT NULL DEFAULT '',`actuator_make` varchar(50) NOT NULL DEFAULT '',`open_torque1` varchar(50) NOT NULL DEFAULT '',`open_torque2` varchar(50) NOT NULL DEFAULT '',`close_torque1` varchar(50) NOT NULL DEFAULT '',`close_torque2` varchar(50) NOT NULL DEFAULT '',`operate_time1` varchar(50) NOT NULL DEFAULT '',`operate_time2` varchar(50) NOT NULL DEFAULT '',`operate_time3` varchar(50) NOT NULL DEFAULT '',`date_time` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',`actuator_tag_no` varchar(50) NOT NULL DEFAULT '',`rated_torque` varchar(50) NOT NULL DEFAULT '',`cycle_complete` ENUM('0','1') NOT NULL DEFAULT '1') ENGINE=INNODB DEFAULT CHARSET=latin1")
teslead_db.commit()
# teslead_db.execute("INSERT INTO qnq_completed." + current_status + " (id,sales_order_no,sales_item_no,valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type,created_on,type_code,type_name,pressure_range,cycle_complete) SELECT id,sales_order_no,sales_item_no,valve_serial_number,pressure,hydro_pressure,date_time,start_graph,test_type,created_on,type_code,type_name,pressure_range,cycle_complete FROM current_status WHERE cycle_complete = '0'")
# teslead_db.commit()
# teslead_db.execute("INSERT INTO qnq_completed." + pressure_analysis + " (id,temprature,set_pressure,max_pressure,pressure_unit,pressure,hydro_pressure,result_pressure,gauge_drop,valve_size,valve_type,valve_class,tested_by,approved_by,valve_tag_no,valve_serial_number,set_time_unit,set_time,actual_time,test_type,write_hmi,START,END,cycle_start,cycle_end,valve_status,STATUS,date_time,start_graph,type_code,type_name,pressure_range,shell_material,sales_order_no,sales_item_no,gad_no,stem_orientation,gear_actuator,ma_gear_ratio,ga_drg_no,appilicability,body_heat,body_mp,body_rt,bonnet_heat,bonnet_mp,bonnet_rt,extn_heat,extn_mp,extn_rt,hydro_1,hydro_2,air_1,air_2,others_1,others_2,others_3,cal_due_hydro_1,cal_due_hydro_2,cal_due_air_1,cal_due_air_2,cal_due_others_1,cal_due_others_2,cal_due_others_3,ep_success,send_status,cycle_complete,ip_address) SELECT id,temprature,set_pressure,max_pressure,pressure_unit,pressure,hydro_pressure,result_pressure,gauge_drop,valve_size,valve_type,valve_class,tested_by,approved_by,valve_tag_no,valve_serial_number,set_time_unit,set_time,actual_time,test_type,write_hmi,START,END,cycle_start,cycle_end,valve_status,STATUS,date_time,start_graph,type_code,type_name,pressure_range,shell_material,sales_order_no,sales_item_no,gad_no,stem_orientation,gear_actuator,ma_gear_ratio,ga_drg_no,appilicability,body_heat,body_mp,body_rt,bonnet_heat,bonnet_mp,bonnet_rt,extn_heat,extn_mp,extn_rt,hydro_1,hydro_2,air_1,air_2,others_1,others_2,others_3,cal_due_hydro_1,cal_due_hydro_2,cal_due_air_1,cal_due_air_2,cal_due_others_1,cal_due_others_2,cal_due_others_3,ep_success,send_status,cycle_complete,ip_address FROM pressure_analysis WHERE cycle_complete = '0'")
# teslead_db.commit()
# teslead_db.execute("INSERT INTO qnq_completed." + master_actuator + " (id,valve_serial_no,actuator_model_main,actuator_model_by_pass1,actuator_model_by_pass2,wiring_diagram_main,wiring_diagram_by_pass1,wiring_diagram_by_pass2,rpm_value_main,rpm_value_by_pass1,rpm_value_by_pass2,oper_time_open_to_close_main,oper_time_open_to_close_by_pass1,oper_time_open_to_close_by_pass2,oper_time_close_to_open_by_main,oper_time_close_to_open_by_pass1,oper_time_close_to_open_by_pass2,act_s_no,torque_setting,bye_pass_valve_sl_no,closing,break_open,eye_bolt_torque,valve_drying,result_drying,remarks,shift,breakaway,media_drained,vent_bleeder,torque_break_nm,torque_run,actuator_make,open_torque1,open_torque2,close_torque1,close_torque2,operate_time1,operate_time2,operate_time3,date_time,actuator_tag_no,rated_torque,cycle_complete)SELECT id,valve_serial_no,actuator_model_main,actuator_model_by_pass1,actuator_model_by_pass2,wiring_diagram_main,wiring_diagram_by_pass1,wiring_diagram_by_pass2,rpm_value_main,rpm_value_by_pass1,rpm_value_by_pass2,oper_time_open_to_close_main,oper_time_open_to_close_by_pass1,oper_time_open_to_close_by_pass2,oper_time_close_to_open_by_main,oper_time_close_to_open_by_pass1,oper_time_close_to_open_by_pass2,act_s_no,torque_setting,bye_pass_valve_sl_no,closing,break_open,eye_bolt_torque,valve_drying,result_drying,remarks,shift,breakaway,media_drained,vent_bleeder,torque_break_nm,torque_run,actuator_make,open_torque1,open_torque2,close_torque1,close_torque2,operate_time1,operate_time2,operate_time3,date_time,actuator_tag_no,rated_torque, cycle_complete FROM master_actuator WHERE cycle_complete = '0'")
# teslead_db.commit()
# teslead_db.execute("DELETE FROM pressure_analysis WHERE cycle_complete = '0'")
# teslead_db.commit()
# teslead_db.execute("DELETE FROM current_status WHERE cycle_complete = '0'")
# teslead_db.commit()
# teslead_db.execute("DELETE FROM master_actuator WHERE cycle_complete = '0'")
# teslead_db.commit()

os.chdir(mysql_db_path)
now = datetime.datetime.now()
os.system("cmd /c mysqldump --database {} --single-transaction --add-drop-database --triggers --routines --events --user=root --password= > D:\\TesleadSmartSyncX\\Database\\{}-{}.sql".format(core_database1, core_database1, now.strftime("%Y-%m-%d")))
os.system("cmd /c mysqldump --database {} --single-transaction --add-drop-database --triggers --routines --events --user=root --password= > D:\\TesleadSmartSyncX\\Database\\{}-{}.sql".format(core_database2, core_database2, now.strftime("%Y-%m-%d")))

def hmi_sync():
    global teslead_db, TesleadSmartSyncX
    clear_cache()
    hmi_ip_address = teslead_db.execute("select ip_address from master_ip_address;").fetchone()[0]
    TesleadSmartSyncX = ModbusTcpClient(hmi_ip_address)
    TesleadSmartSyncX.connect()
hmi_sync()

webbrowser.open("http://localhost/aruna/")

def getstatus(xad):
    global TesleadSmartSyncX
    while True:
        try:
            return TesleadSmartSyncX.read_holding_registers(xad, 1).registers[0]
        except Exception as e:
            print(f'Error getting data : {e}')
            local_db()
            hmi_sync()

def pushstatus(xad, xval):
    global TesleadSmartSyncX
    while True:
        try:
            TesleadSmartSyncX.write_register(int(xad), int(xval))
            return None
        except Exception as e:
            print(f'Error Sending data : {e}')
            local_db()
            hmi_sync()

def main_thread():
    global teslead_db, TesleadSmartSyncX, wait_flag, u0024saPDF, u0024saOnce, u0024saWait
    while True:
        clear_cache()
        actual_time = getstatus(2006)
        actual_pressure = getstatus(2008)
        cycle_start = getstatus(2009)
        start_stop = getstatus(2010)
        valve_status = getstatus(2011)
        auto_manual = getstatus(2012)
        result_pressure = getstatus(2013)
        alarm = getstatus(2017)
        leak_pressure = getstatus(2018)
        test_mode = getstatus(2019)
        hydraulic_pressure = getstatus(2050)
        oring_dia = getstatus(2100)
        u0024sa11 = getstatus(2101)
        u0024sa12 = getstatus(2102)
        u0024sa13 = getstatus(2103)
        u0024sa14 = getstatus(2104)
        get_station_status = teslead_db.execute("select group_concat(id) as id, group_concat(station_status) as status from master_temp_data;").fetchone()
        station_status = get_station_status[1].split(',')
        machine_status = [1 if s == 'active' else 0 for s in station_status]
        station1_status = machine_status[0]
        activate_wait_flag = teslead_db.execute("select count(*) from pressure_analysis where status='1';").fetchall()[0][0]
        if activate_wait_flag >= 1:
            testing_parameters = teslead_db.execute("SELECT pa.ip_address,pa.set_pressure,pa.max_pressure,pa.pressure_unit,pa.set_time_unit,pa.set_time,pa.valve_type,pa.valve_size,pa.valve_class,pa.test_type,pa.shell_material,pa.write_hmi,mvc.valveclass_desc FROM pressure_analysis pa ,master_valveclass mvc WHERE pa.STATUS = '1' AND  pa.valve_class = mvc.valveclass_code;").fetchall()[0]
            clear_cache()
            valve_size = teslead_db.execute(f"select valvesize_code from master_valvesize where valvesize_name = '{testing_parameters[7]}';").fetchone()[0]
            write_hmi = int(testing_parameters[11])
            if write_hmi == 1:
                print("Writing to HMI...")
                print(f"Valve Size : {testing_parameters[7]} and Valve size code : {valve_size}")
                get_pressure_unit = testing_parameters[3]
                if get_pressure_unit == "psi":
                    pressure_unit = 0
                    set_pressure = int(testing_parameters[1])
                if get_pressure_unit == "bar":
                    pressure_unit = 1
                    set_pressure = int(testing_parameters[1] * 10)
                # valve_size = int(testing_parameters[7])
                valve_class = int(testing_parameters[8])
                set_time = int(testing_parameters[5])
                test_type = int(testing_parameters[9])
                u0024sa11 = 1
                u0024sa12 = 1
                u0024sa13 = 1
                u0024sa14 = 1
                pushstatus(2170, pressure_unit)
                pushstatus(2000, set_pressure)
                pushstatus(2001, valve_size)
                pushstatus(2002, valve_class)
                pushstatus(2003, set_time)
                pushstatus(2004, test_type)
                pushstatus(2101, u0024sa11)
                pushstatus(2102, u0024sa12)
                pushstatus(2103, u0024sa13)
                pushstatus(2104, u0024sa14)
                print(f"Sending Status :- Set Pressure : {set_pressure}, Valve Size : {valve_size}, Valve Class : {valve_class}, Set Time : {set_time}, Test Type : {test_type}, S1x{u0024sa11}{u0024sa12}{u0024sa13}{u0024sa14}")
                teslead_db.execute("update pressure_analysis set write_hmi=0 where status='1';")
            wait_flag = 1
        elif activate_wait_flag == 0:
            if u0024saWait == 1:
                print("Wait...")
                u0024saWait = 0
            wait_flag = 0
            get_count = teslead_db.execute("select count(*) from pressure_analysis;").fetchall()[0][0]
            if get_count > 0 and u0024saOnce == 1:
                u0024saPDF = 1
                u0024saOnce = 0
            if u0024saPDF == 1:
                pdf_array = teslead_db.execute("select valve_serial_number, date_time from pressure_analysis order by id desc limit 1;").fetchall()[0]
                if len(pdf_array) > 0:
                    serial_number = pdf_array[0]
                    get_date_time = pdf_array[1]
                    temp_date_time = get_date_time.strftime("%d_%m_%Y_%H_%M")
                    matching_files = []
                    name_serial_date = f'Aruna_Excel_Report_{serial_number}_{temp_date_time}.xlsx'
                    for filename in os.listdir(local_reports_path):
                        if name_serial_date in filename:
                            matching_files.append(filename)
                    if matching_files:
                        print(len(matching_files))
                        print("Files containing the filename:")
                        for file in matching_files:
                            print(file)
                    else:
                        print(f"No files found containing the filename as {name_serial_date}")
                    def convert_xlsx_to_pdf(xlsx_file, pdf_file):
                        excel = win32com.client.Dispatch("Excel.Application")
                        excel.Visible = True 
                        try: 
                            workbook = excel.Workbooks.Open(xlsx_file)
                            for sheet in workbook.Sheets:
                                sheet.PageSetup.PaperSize = 9 
                                sheet.PageSetup.Orientation = 2 
                                sheet.PageSetup.Zoom = False 
                                sheet.PageSetup.FitToPagesWide = 1 
                                sheet.PageSetup.FitToPagesTall = 1 
                                sheet.PageSetup.LeftMargin = excel.Application.InchesToPoints(0.2)
                                sheet.PageSetup.RightMargin = excel.Application.InchesToPoints(0.2) 
                                sheet.PageSetup.TopMargin = excel.Application.InchesToPoints(0.2)  
                                sheet.PageSetup.BottomMargin = excel.Application.InchesToPoints(0.2) 
                                sheet.PageSetup.CenterFooter = "" 
                                sheet.PageSetup.LeftFooter = ""  
                                sheet.PageSetup.RightFooter = ""   
                            workbook.ExportAsFixedFormat(0, pdf_file)  
                            workbook.Close(False)
                            excel.Quit()
                        except Exception as e:
                            print(f"Error converting Excel to PDF : {e}")
                            excel.Quit()
                    xlsx_file = f'{local_reports_path}/Aruna_Excel_Report_{serial_number}_{temp_date_time}.xlsx'
                    pdf_file = f'{local_excel_pdf_path}/Aruna_Excel_Report_{serial_number}_{temp_date_time}.pdf'
                    print(f"Length of matching files : {len(matching_files)}")
                    if len(matching_files) > 0 and u0024saPDF == 1:
                        convert_xlsx_to_pdf(xlsx_file, pdf_file)
                        print("Conversion completed")
                        u0024saPDF = 0       #Wait PDF
        if wait_flag == 1:
            u0024saPDF = 1
            teslead_db.execute(f"update master_ip_address SET auto_manual={auto_manual};")
            teslead_db.commit()
            teslead_db.execute(f"update alarm set code={alarm} where status=0;")
            
            if cycle_start == 1 and u0024sa13 == 1 and station1_status == 1:         # Condition 1
                teslead_db.execute("update pressure_analysis set pressure=%s, hydro_pressure=%s, result_pressure=%s, actual_time=%s, valve_status=%s, extn_rt=%s, cycle_start=NOW(), date_time=NOW(), start_graph=0 where status='1' and station_status='1';" % (actual_pressure, hydraulic_pressure, result_pressure, actual_time, valve_status, oring_dia))
                teslead_db.commit()
                teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                teslead_db.commit()
                u0024sa13 = 0
                u0024sa14 = 0
                pushstatus(2102, u0024sa13)
                pushstatus(2103, u0024sa14) 
                
            if cycle_start == 0 and u0024sa13 == 0 and station1_status == 1:         # Condition 2
                teslead_db.execute("update pressure_analysis set pressure=%s, hydro_pressure=%s, result_pressure=%s, actual_time=%s, valve_status=%s, extn_rt=%s, cycle_end=NOW(), date_time=NOW(), start_graph=0 where status='1' and station_status='1';" % (actual_pressure, hydraulic_pressure, result_pressure, actual_time, valve_status, oring_dia))
                teslead_db.commit()
                teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                teslead_db.commit()
                u0024sa13 = 1
                u0024sa14 = 1
                pushstatus(2102, u0024sa13)
                pushstatus(2103, u0024sa14)

            if cycle_start == 1 and start_stop == 0 and station1_status == 1:        # Condition 3
                teslead_db.execute("update pressure_analysis set pressure=%s, hydro_pressure=%s, result_pressure=%s, actual_time=%s, valve_status=%s, extn_rt=%s, date_time=NOW(), start_graph=0 where status='1' and station_status='1';" % (actual_pressure, hydraulic_pressure, result_pressure, actual_time, valve_status, oring_dia))
                teslead_db.commit()
                teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                teslead_db.commit()

            if start_stop == 1 and u0024sa11 == 1:   # Condition 4
                if station1_status == 1:
                    teslead_db.execute("update pressure_analysis set pressure=%s, start_pressure=%s, actual_time=%s, start=NOW(), valve_status=%s, extn_rt=%s, start_graph=1, date_time=NOW() where status='1' and station_status='1';" % (actual_pressure, actual_pressure, actual_time, valve_status, oring_dia))
                    teslead_db.commit()
                    teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                    teslead_db.commit()
                    u0024sa11 = 0
                    u0024sa12 = 0
                    pushstatus(2101, u0024sa11)
                    pushstatus(2102, u0024sa12)

            if start_stop == 1:                                  # Condition 5
                if station1_status == 1:
                    teslead_db.execute("update pressure_analysis set pressure=%s, hydro_pressure=%s, actual_time=%s, valve_status=%s, extn_rt=%s, start_graph=1, date_time=NOW() where status='1' and station_status='1';" % (actual_pressure, hydraulic_pressure, actual_time, valve_status, oring_dia))
                    teslead_db.commit()
                    teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                    teslead_db.commit()

            if start_stop == 0 and u0024sa12 == 0:           # Condition 6
                if station1_status == 1:
                    teslead_db.execute("update pressure_analysis set pressure=%s, result_pressure=%s, gauge_drop=%s, end=NOW(), valve_status=%s, extn_rt=%s, start_graph=1, date_time=NOW() where status='1' and station_status='1';" % (actual_pressure, result_pressure, leak_pressure, valve_status, oring_dia))
                    teslead_db.commit()
                    teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                    teslead_db.commit()
                    u0024sa12 = 1
                    u0024sa11 = 1
                    pushstatus(2102, u0024sa12)
                    pushstatus(2101, u0024sa11)

            if start_stop == 0 and cycle_start == 0 and station1_status == 1:                # Condition 7
                teslead_db.execute("update pressure_analysis set pressure=%s, hydro_pressure=%s, extn_rt=%s, start_graph=0, date_time=NOW() where status='1' and station_status='1';" % (actual_pressure, hydraulic_pressure, oring_dia))
                teslead_db.commit()
                teslead_db.execute("insert into current_status (sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type) select sales_order_no, sales_item_no, valve_serial_number, pressure, hydro_pressure, date_time, start_graph, test_type from pressure_analysis where status='1' and station_status='1';")
                teslead_db.commit()
        time.sleep(1)
root = tk.Tk()
label = tk.Label(root, text="Running...")
ByteImage = Image.open("E:\\EXE\\teslead-logo.png")
ByteImage = ByteImage.resize((150, 50), Image.Resampling.BICUBIC)
PulseImage = ImageTk.PhotoImage(ByteImage)
label = tk.Label(root, image=PulseImage)
label.image = PulseImage
label.pack()
root.overrideredirect(True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 150
window_height = 50
x = (screen_width/2) - (window_width/2)
y = (screen_height/2) - (window_height/2)
root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")
thread_main = threading.Thread(target=main_thread)
thread_main.daemon = False
thread_main.start()
print("Program Completed")
root.mainloop()