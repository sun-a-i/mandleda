


#con_list = {"000": {"name": "1번 조건식", "list" : ["123556","123123"] }}

con_list = {}
con_list["000"] = {}
con_list["000"]["name"] = "1번조건식"
con_list["000"]["dic"] = {"123556":"123123"}

print(con_list)
print(con_list["000"]["name"])
print(con_list["000"]["dic"])


for i in con_list:

    a = i+con_list[i]["name"]

print(a[:3])