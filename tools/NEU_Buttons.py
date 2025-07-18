from pyperclip import copy, paste
from base64 import b64encode, b64decode
from json import dumps

#b'NEUBUTTONS/["{\\n  \\"x\\": 87,\\n  \\"y\\": 63,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 108,\\n  \\"y\\": 63,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 129,\\n  \\"y\\": 63,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 150,\\n  \\"y\\": 63,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 87,\\n  \\"y\\": 5,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 108,\\n  \\"y\\": 5,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 129,\\n  \\"y\\": 5,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 150,\\n  \\"y\\": 5,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 87,\\n  \\"y\\": 25,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 105,\\n  \\"y\\": 25,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 87,\\n  \\"y\\": 43,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 105,\\n  \\"y\\": 43,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 143,\\n  \\"y\\": 35,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 60,\\n  \\"y\\": 8,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 60,\\n  \\"y\\": 60,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 26,\\n  \\"y\\": 8,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 26,\\n  \\"y\\": 60,\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": 22,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": 42,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": 62,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": -84,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": -64,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\",\\n  \\"icon\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": -44,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 2,\\n  \\"y\\": -24,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": true,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 4,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"warp island\\",\\n  \\"icon\\": \\"BIRD_HOUSE\\"\\n}","{\\n  \\"x\\": 25,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 46,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 67,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 88,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 109,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 130,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 151,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": 22,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": 42,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": 62,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": -84,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": -64,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": -44,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": TOP_START[1],\\n  \\"y\\": -24,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 4,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 25,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 46,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 67,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 88,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 109,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 130,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}","{\\n  \\"x\\": 151,\\n  \\"y\\": 2,\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": true,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"\\"\\n}"]'

#"{\\n  \\"x\\": 4,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"warp island\\",\\n  \\"icon\\": \\"BIRD_HOUSE\\"\\n}"

TOP_START = (-14, -19) # (4, -19)
GAP = 20

sData = [
    ### TOP ###
    {
        "x": TOP_START[0],
        "y": TOP_START[1],
        "command": "warp island",
        "icon": "BIRD_HOUSE"
    },
    {
        "x": TOP_START[0]+GAP,
        "y": TOP_START[1],
        "command": "warp hub",
        "icon": "skull:c9c8881e42915a9d29bb61a16fb26d059913204d265df5b439b3d792acd56"
    },
    {
        "x": TOP_START[0]+GAP*2,
        "y": TOP_START[1],
        "command": "warp dragons",
        "icon": "skull:7840b87d52271d2a755dedc82877e0ed3df67dcc42ea479ec146176b02779a5"
    },
    {
        "x": TOP_START[0]+GAP*3,
        "y": TOP_START[1],
        "command": "warp deep",
        "icon": "skull:569a1f114151b4521373f34bc14c2963a5011cdc25a6554c48c708cd96ebfc"
    },
    {
        "x": TOP_START[0]+GAP*4,
        "y": TOP_START[1],
        "command": "warp spiders",
        "icon": "DANGER_1_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*5,
        "y": TOP_START[1],
        "command": "warp crimson",
        "icon": "DANGER_2_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*6,
        "y": TOP_START[1],
        "command": "warp park",
        "icon": "skull:79ca3540621c1c79c32bf42438708ff1f5f7d0af9b14a074731107edfeb691c"
    },
    {
        "x": TOP_START[0]+GAP*7,
        "y": TOP_START[1],
        "command": "warp castle",
        "icon": "HUB_CASTLE_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*8,
        "y": TOP_START[1],
        "command": "warp desert",
        "icon": "SAND"
    },
    ### TOP 2 LAYER ###
    {
        "x": TOP_START[0]+GAP*0,
        "y": TOP_START[1]-GAP*1,
        "command": "warp garden",
        "icon": "FARMING_TALISMAN"
    },
    {
        "x": TOP_START[0]+GAP*1,
        "y": TOP_START[1]-GAP*1,
        "command": "warp nucleus",
        "icon": "FINE_RUBY_GEM"
    },
    {
        "x": TOP_START[0]+GAP*2,
        "y": TOP_START[1]-GAP*1,
        "command": "warp dwarves",
        "icon": "DWARVEN_MINES_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*3,
        "y": TOP_START[1]-GAP*1,
        "command": "warp forge",
        "icon": "ANVIL"
    },
    {
        "x": TOP_START[0]+GAP*4,
        "y": TOP_START[1]-GAP*1,
        "command": "warp tunnels",
        "icon": "BASE_CAMP_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*5,
        "y": TOP_START[1]-GAP*1,
        "command": "warp workshop",
        "icon": "skull:6dd663136cafa11806fdbca6b596afd85166b4ec02142c8d5ac8941d89ab7"
    },
    {
        "x": TOP_START[0]+GAP*6,
        "y": TOP_START[1]-GAP*1,
        "command": "warp bayou",
        "icon": "FISHING_1_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*7,
        "y": TOP_START[1]-GAP*1,
        "command": "warp crypt",
        "icon": "HUB_CRYPTS_PORTAL"
    },
    {
        "x": TOP_START[0]+GAP*8,
        "y": TOP_START[1]-GAP*1,
        "command": "warp dungeons",
        "icon": "skull:9b56895b9659896ad647f58599238af532d46db9c1b0389b8bbeb70999dab33d"
    },

    ### LEFT SIDE ###

    {
        "x": TOP_START[1]+GAP*0,
        "y": 2-GAP*0,
        "command": "skills",
        "icon": "DIAMOND_SWORD"
    },
    {
        "x": TOP_START[1]+GAP*0,
        "y": 2+GAP*1,
        "command": "collections",
        "icon": "PAINTING"
    },
    {
        "x": TOP_START[1]+GAP*0,
        "y": 2+GAP*2,
        "command": "attributemenu",
        "icon": "BEACON"
    },
    ### SMALL LEFT SIDE ###
    {
        "x": TOP_START[1]+GAP*0,
        "y": -44+GAP*0,
        "command": "craft",
        "icon": "WORKBENCH",
        "anchorBottom": True,
    },
    {
        "x": TOP_START[1]+GAP*0,
        "y": -44+GAP*1,
        "command": "anvil",
        "icon": "ANVIL",
        "anchorBottom": True,
    },

    ### RIGHT SIDE ###

    {
        "x": 2+GAP*0,
        "y": 2+GAP*0,
        "command": "ec",
        "icon": "ENDER_CHEST",
        "anchorRight": True
    },
    {
        "x": 2+GAP*0,
        "y": 2+GAP*1,
        "command": "sacks",
        "icon": "MEDIUM_COMBAT_SACK",
        "anchorRight": True
    },
    {
        "x": 2+GAP*0,
        "y": 2+GAP*2,
        "command": "wardrobe",
        "icon": "DIAMOND_CHESTPLATE",
        "anchorRight": True
    },
    {
        "x": 2+GAP*0,
        "y": 2+GAP*3,
        "command": "pets",
        "icon": "BONE",
        "anchorRight": True
    },
    {
        "x": 2+GAP*0,
        "y": 2+GAP*4,
        "command": "hotm",
        "icon": "skull:86f06eaa3004aeed09b3d5b45d976de584e691c0e9cade133635de93d23b9edb",
        "anchorRight": True
    },

    ### recipe ###
    {
        "x": 143,
        "y": 35 + 18,
        "command": "recipe",
        "icon": "CRAFTING_PLUS"
    },

]



data = {
    "playerInvOnly": True,
    "anchorRight": False,
    "anchorBottom": False,
    "backgroundIndex": 1,
}

try:
    oldData = paste()
    for i in b64decode(oldData).split(b"icon")[1:]:
        b = i.split(b"\\\"")[2]
        if b == b"":
            continue
        print(b)
    print(b64decode(oldData))
except: pass

list_ = []

for d in sData:
    _data = data.copy()
    _data.update(d)
    print(_data)
    jsStr = dumps(_data, indent=2)
    jsStr = jsStr.replace("\"", "\\\"")
    print(repr(jsStr))
    list_.append(jsStr)

jsBytes = str(list_).encode().replace(b"\'", b"\"").replace(b"\\\\", b"\\")


#print(b64encode(b'NEUBUTTONS/["{\\n  \\"x\\": 4,\\n  \\"y\\": TOP_START[1],\\n  \\"playerInvOnly\\": false,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1,\\n  \\"command\\": \\"warp island\\",\\n  \\"icon\\": \\"BIRD_HOUSE\\"\\n}"]'))

# GOOD: b'NEUBUTTONS/["{\n  \\"playerInvOnly\\": true,\n  \\"anchorRight\\": false,\n  \\"anchorBottom\\": false,\n  \\"backgroundIndex\\": 1\n}"]'
#       b'NEUBUTTONS/["{\\n  \\"playerInvOnly\\": true,\\n  \\"anchorRight\\": false,\\n  \\"anchorBottom\\": false,\\n  \\"backgroundIndex\\": 1\\n}"]'


bytes_ = b'NEUBUTTONS/' + jsBytes
print(bytes_)
b64Enc = b64encode(bytes(bytes_))

copy(b64Enc.decode())

