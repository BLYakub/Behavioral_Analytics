# import win32net,time

# users,nusers,_ = win32net.NetUserEnum(None,2)
# for user in users:
#     print(user['name'],time.ctime(user['last_logoff']))
import win32api
import datetime

# # Get the current tick count and idle time
# current_tick_count = win32api.GetTickCount()
# # idle_time = win32api.GetIdleTime()
# last_input_info = win32api.GetLastInputInfo()
# idle_time = current_tick_count - last_input_info
# # Calculate the last logout time
# last_logout_time = current_tick_count - idle_time

# # Print the last logout time
# print(f"Last logout time: {last_logout_time}")

# # Convert the last logout time to a timestamp
# last_logout_timestamp = datetime.datetime.fromtimestamp(last_logout_time / 1000.0)

# # Print the last logout timestamp
# print(f"Last logout timestamp: {last_logout_timestamp}")


import browserhistory as bh

dict_obj = bh.get_browserhistory()
print(dict_obj['chrome'])
# dict_keys(['safari', 'chrome', 'firefox'])
# print(dict_obj['safari'][0])



