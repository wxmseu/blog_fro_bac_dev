# class Chain(object):
#
#     def __init__(self, path=''):
#         self._path = path
#
#     def __getattr__(self, path):
#         return Chain('%s/%s' % (self._path, path))
#
#     def __str__(self):
#         return self._path
#
#     __repr__ = __str__
#
#
# print(Chain().status.user.timeline.list)
# 源数据
s = [{'name': 'leader-1', 'belong_to': None}, {'name': 'jack', 'belong_to': 'leader-2'},
     {'name': 'lili', 'belong_to': 'leader-1'}, {'name': 'leader-2', 'belong_to': None},
     {'name': 'Tom', 'belong_to': 'leader-1'}]
# 目标数据
d = [
    {'name': 'leader-1', 'team': [{'name': 'lili'}, {'name': 'Tom'}]},
    {'name': 'leader-2', 'team': [{'name': 'jack'}]}
]
def find_team(s):
    d=[]
    team1=[]
    team2=[]
    for person in s:
        if person['belong_to']=='leader-1':
            team1.append({'name':person['name']})
        elif person['belong_to']=='leader-2':
            team2.append({'name':person['name']})
        else:
            continue
    return [
    {'name': 'leader-1', 'team': team1},
    {'name': 'leader-2', 'team':team2}
]

print(find_team(s))

