
# importing the tkinter module and PIL
# that is pillow module
import copy
from dataclasses import dataclass
import dataclasses
from genericpath import exists
import glob
import json
import math
from textwrap import indent
from tkinter import *
from PIL import ImageTk, Image

class_name_shortcut = {
        "s": "Sella",
        "n": "Naison",
        "a":"A-point",
        "b":"B-point",
        "ga":"Glabella",
        "go":"Gonion",
        "me":"Menton",
        "po":"Porion",
        "or":"Orbitale",
        "u1i":"U1-inc",
        "u1a":"U1-apex",#
        "l1i":"L1-inc",
        "l1a":"L1-apex",
        "u6":"U6-mbc",#
        "l6":"L6-mbc"
}
inv_class_name_shortcut = {v: k for k, v in class_name_shortcut.items()}

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)
            
def reset_state_full():
    global state
    global canvas
    global label_active_class
    state = copy.deepcopy(state_default)
    # delete all the lines
    canvas.delete('line')
    canvas.delete('circle')
    canvas.delete('bisector_circle')
    canvas.delete('tmp_bisector_circle')
    for state_class in state['classes'][1:]:
        canvas.delete(state_class['name'])
    if label_active_class is not None:
        label_active_class.destroy()

def reset_state_part():
    global state
    global canvas

    for i, state_class in enumerate(state['classes']):
        if state_class['name'] == state['active_class']:
            if state_class['name'] != 'Gonion':
                canvas.delete(state_class['name'])
            else:
                canvas.delete('line')
                canvas.delete('circle')
                canvas.delete('bisector_circle')
                canvas.delete('tmp_bisector_circle')
            state_class= copy.deepcopy(state_default['classes'][i])
            state['classes'][i] = state_class
    make_table()

def create_circle(canvasName,x, y, r=2,tag = 'circle',color = 'black'): #center coordinates, radius
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvasName.create_oval(x0, y0, x1, y1,tag = tag,fill = color)

def create_line(canvas,x_1, y_1, x_2, y_2,color='yellow',width=2):
    global canvas_width
    # use equation of a line to extend the line to the end of the canvas, while maintaining the same slope

    m = (y_2 - y_1) / (x_2 - x_1) if (x_2 - x_1) != 0 else 1e10
    b = y_1 - m * x_1
    x_end = MAX_SIZE
    y_end = m * x_end + b
    x_start = 0
    y_start = m * x_start + b
    canvas.create_line(x_start, y_start, x_end, y_end,width=width,fill=color,tag='line')
@dataclass
class Point:
    x: int
    y: int
    __point__:bool = True

def on_button_1_clicked(tk_event):
    global state
    global canvas
    # print("Button 1 clicked",tk_event)
    if state['active_class'] == 'Gonion':
        state_gonion = state['classes'][0]
        if state_gonion['first_line'] == False:
            state_gonion['first_line'] = [Point(tk_event.x,tk_event.y)]
            create_circle(canvas,tk_event.x,tk_event.y)
            print("First line")
        elif len(state_gonion['first_line']) == 1:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['first_line'] = [state_gonion['first_line'][0], Point(tk_event.x,tk_event.y)]
            create_line(canvas, state_gonion['first_line'][0].x, state_gonion['first_line'][0].y, tk_event.x, tk_event.y)
            print("First line")
        elif state_gonion['second_line'] == False:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['second_line'] = [Point(tk_event.x,tk_event.y)]
            print("Second line")
        elif len(state_gonion['second_line']) == 1:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['second_line'] = [state_gonion['second_line'][0], Point(tk_event.x,tk_event.y)]
            print("Second line")
            create_line(canvas, state_gonion['second_line'][0].x, state_gonion['second_line'][0].y, tk_event.x, tk_event.y)
            create_angle_bisector(canvas)
        elif state_gonion['third_mouse_click'] == False:

            state_gonion['third_mouse_click'] = Point(tk_event.x,tk_event.y)
            x,y,c =  state_gonion['bisector']
            x_pos,y_pos = get_circle_loc_on_bisector(tk_event, x, y, c)
            state_gonion['gonion_point'] = [x_pos,y_pos]
            create_circle(canvas,x_pos,y_pos,r=2,tag='bisector_circle',color='yellow')
            state_gonion['bisector_draw'] = False
            print("Third line")
        state['classes'][0] = state_gonion
    else:
        for state_class in state['classes']:
            if state_class['name'] == state['active_class']:
                state_class['pos'] = Point(tk_event.x,tk_event.y)
                canvas.delete(state_class['name'])
                create_circle(canvas,tk_event.x,tk_event.y,tag=state_class['name'],color=state_class['color'])
                state['classes'][state['classes'].index(state_class)] = state_class
                break
    make_table()
    

def create_angle_bisector(canvas):
    global state
    state_gonion = state['classes'][0]
    first_line = state_gonion['first_line']
    second_line = state_gonion['second_line']
    x, y, c = get_line_bisector_params(first_line, second_line,-1)
    m = x/y if y != 0 else 1e10
    if m<0:
        x, y, c = get_line_bisector_params(first_line, second_line,1)
    x_intercept = -c/x if x!=0 else 1e10
    y_intercept = -c/y if y!=0 else 1e10
    state_gonion['bisector'] = [x,y,c]
    state_gonion['bisector_draw'] = True
    create_line(canvas, 0, y_intercept,x_intercept, 0,color='red',width=1)
    state['classes'][0] = state_gonion

def get_line_bisector_params(first_line, second_line,multiplier=1):
    a1, b1, c1  = get_line_equation(first_line[0].x, first_line[0].y, first_line[1].x, first_line[1].y)
    a2, b2, c2  = get_line_equation(second_line[0].x, second_line[0].y, second_line[1].x, second_line[1].y)
    right_term = multiplier*math.sqrt(a1**2 + b1**2)/math.sqrt(a2**2 + b2**2) if math.sqrt(a2**2 + b2**2) != 0 else 1e10*multiplier*math.sqrt(a1**2 + b1**2)
    x = a1-a2*right_term
    y = b1-b2*right_term
    c = c1-c2*right_term

    return x,y,c


def get_line_equation(x1, y1, x2, y2):
    a = y2 - y1
    b = x1 - x2
    c = x2 * y1 - x1 * y2
    return a, b, c

def draw_hover_circle(event):
    global state
    global canvas
    state_gonion = state['classes'][0]
    if state_gonion['bisector_draw']!=False:
        x,y,c = state_gonion['bisector']
        event_x, y_pos = get_circle_loc_on_bisector(event, x, y, c)
        canvas.delete('tmp_bisector_circle')
        create_circle(canvas,event_x,y_pos,r=2,tag='tmp_bisector_circle')
    else:
        create_circle(canvas,1,1,r=10)
                


def get_circle_loc_on_bisector(event, x, y, c):
    event_x = event.x
    y_pos = -(event_x*x + c)/y
    return event_x,y_pos

def leftKey(event):
    global left_key_func
    if left_key_func != None:
        left_key_func(event)

def rightKey(event):
    global right_key_func
    if right_key_func != None:
        right_key_func(event)

def change_class_func(event,name):
    print(name)
    global state
    global label_active_class

    state['active_class'] = name
    label_active_class.config(text=f"Active class: {state['active_class']}")
    active_class = [state_class for state_class in state['classes'] if state_class['name'] == name][0]
    label_active_class.config(fg=active_class['color'])

def create_canvas(image):
    global root
    canvas = Canvas(root, width=MAX_SIZE, height =MAX_SIZE )
    # We have to show the the box so this below line is needed

    canvas.create_image(10, 10, anchor=NW, image=image)
    canvas.grid(row=1, column=0, columnspan=4)
    canvas.bind("<Button-1>", on_button_1_clicked)
    canvas.bind('<Motion>', draw_hover_circle)
    canvas.bind('<Enter>', draw_hover_circle) 
    root.bind('<Left>', leftKey)
    root.bind('<Right>', rightKey)
    # root.bind('<Key>', key_pressed)
    for k, v in class_name_shortcut.items():
        root.bind(k, lambda event, name=v: change_class_func(event, name))

    return canvas

def save_state(image_path,current_path):
    global state
    # open json file and save current state in it
    with open('db.json', 'r') as f:
        db = json.load(f)
        db['data'][image_path] = state
        db['current_image'] = current_path
    with open('db.json', 'w') as f:
        json.dump(db, f,cls=EnhancedJSONEncoder,indent=4)

def decode_point(dct):
    if "__point__" in dct:
        return Point(dct["x"], dct["y"])
    else:
        return dct

def load_state(image_path):
    global state
    global canvas
    reset_state_full()
    # open json file and load state from it
    with open('db.json', 'r') as f:
        db = json.load(f,object_hook=decode_point)

        if image_path in db['data']:
            state = db['data'][image_path]
            for state_class in state['classes']:
                if state_class['name'] == 'Gonion':
                    if state_class['first_line'] !=False:
                        line = state_class['first_line']
                        redraw_line(line)
                    if state_class['second_line'] !=False:
                        line = state_class['second_line']
                        redraw_line(line)
                        if len(line) == 2:
                            create_angle_bisector(canvas)
                    if state_class['third_mouse_click'] !=False:
                        x,y,c =  state_class['bisector']
                        x_pos,y_pos = get_circle_loc_on_bisector(state_class['third_mouse_click'], x, y, c)
                        create_circle(canvas,x_pos,y_pos,r=2,tag='bisector_circle',color='yellow')
                        state_class['bisector_draw'] = False
                else:
                    if state_class['pos']!=False:
                        create_circle(canvas,state_class['pos'].x,state_class['pos'].y,tag=state_class['name'],color=state_class['color'])
                        

def forward(img_path):
    global canvas
    global button_forward
    global button_back
    global button_clear
    global state
    global img_paths
    global label_active_class
    global current_image
    global current_image_path

    canvas.grid_forget()

    save_state(current_image_path,img_path)
    current_image_path = img_path

    current_image = create_image_from_path(img_path)
    current_image_path = img_path
    canvas = create_canvas(current_image)

    load_state(current_image_path)
    create_forward_button(img_path)
    create_back_button(img_path)


    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'],background='black')

    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)
    make_table()
def create_forward_button(img_path):
    global button_forward
    global right_key_func
    if img_paths.index(img_path) == len(img_paths)-1:
        button_forward = Button(root, text="Forward",
                                state=DISABLED)
        right_key_func = lambda event: None
    else:
        button_forward = Button(root, text="forward",
                        command=lambda: forward(img_paths[img_paths.index(img_path)+1]))
        right_key_func = lambda event: forward(img_paths[img_paths.index(img_path)+1])

    

def back(img_path):

    global canvas
    global button_forward
    global button_back
    global button_clear
    global label_active_class
    global state
    global img_paths
    global current_image
    global current_image_path

    canvas.grid_forget()
    save_state(current_image_path,img_path)
    current_image_path = img_path
    # for clearing the image for new image to pop up
    current_image = create_image_from_path(img_path)
    current_image_path = img_path
    canvas = create_canvas(current_image)
    load_state(current_image_path)
    create_forward_button(img_path)
    create_back_button(img_path)

    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'],background='black')

    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)
    make_table()

def create_back_button(img_path):
    global button_back
    global left_key_func

    if img_paths.index(img_path) == 0:
        button_back = Button(root, text="Back", state=DISABLED)
        left_key_func = lambda event: None
    else:
        button_back = Button(root, text="Back",command=lambda: back(img_paths[img_paths.index(img_path)-1]))
        left_key_func = lambda event: back(img_paths[img_paths.index(img_path)-1])

def main():
    global root
    root = Tk()
    root.title("Dental Image classifier")
    root.geometry("1000x1000")

    #define the global vars
    global img_paths
    global canvas
    global button_forward
    global button_back
    global button_clear
    global label_active_class
    global current_image
    global current_image_path
    global left_key_func
    global right_key_func

    img_paths = glob.glob("images/*.jpg")
    img_paths.extend(glob.glob("images/*.JPG"))

    if exists('db.json'):
        with open('db.json', 'r') as f:
            db = json.load(f)
    else:
        db = {
            "current_image":img_paths[0],
            "data":{}
        }
        json.dump(db, open('db.json', 'w'),indent=4)
    current_image_path = db['current_image'] if db['current_image'] in img_paths else img_paths[0]
    current_image = create_image_from_path(current_image_path)
    canvas = create_canvas(current_image)
    label_active_class = None
    load_state(current_image_path)


    create_forward_button(current_image_path)
    create_back_button(current_image_path)

    button_clear = Button(root, text="Clear", command=reset_state_part)

    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'],background='black')
 
    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)
    make_table()

    root.mainloop()

def make_table():
    global state
    global root
    global canvas

    state_char_map = {
        True:'X',
        False:'V'
    }
    data = [[f"{i['name']} ({inv_class_name_shortcut[i['name']]})",state_char_map[i['pos']==False]] for i in state['classes'] if i['name'] != 'Gonion' ]
    state_gonion = [i for i in state['classes'] if i['name'] == 'Gonion'][0]
    data.append([f"Gonion ({inv_class_name_shortcut['Gonion']})" ,state_char_map[state_gonion['gonion_point']==False]])

    t = Table(root,data)

    t.frame1.grid(row=1, column=6)
    #change_class_func(None,state["active_class"])
    #root.update()
    #canvas.focus_set()
    create_circle(canvas,0,0)
def create_image_from_path(image):
    pil_im = Image.open(image)
    pil_im = pil_im.resize((MAX_SIZE, MAX_SIZE), Image.ANTIALIAS)
    im =ImageTk.PhotoImage(pil_im)
    return im

MAX_SIZE = 800

def make_state_default(class_name_shortcut):
    state_default = {
    'active_class': 'Gonion',
    'classes':[
        {
            'name': 'Gonion',
            "first_line": False,
            "second_line": False,
            "third_mouse_click": False,
            "bisector":False,
            'bisector_draw': False,
            'color': 'orange',
            'gonion_point': False,
        }
        # ,
        # {
        #     'name': 'second_class',
        #     'color': 'blue', 
        #     'pos':False
        # }
        ]
    }
    colors = [ "red", "green", "SeaGreen", "cyan", "yellow", "magenta","HotPink1","BlueViolet","burlywood4","OrangeRed","goldenrod","DarkSlateGrey","MistyRose4","olive"]
    c_dict = {k:v for k,v in class_name_shortcut.items() if v!= 'Gonion'}
    for i, (k,v) in enumerate(c_dict.items()):
        state_default['classes'].append({
        'name': v,
        'color': colors[i%len(colors)],
        'pos':False
    })
    return state_default

state_default = make_state_default(class_name_shortcut)

def redraw_line(line):
    for line_event in line:
        create_circle(canvas,line_event.x,line_event.y)
    if len(line) == 2:
        create_line(canvas, line[0].x, line[0].y, line[1].x, line[1].y)

class Table:
     
    def __init__(self,root,lst):
        self.frame1 = Frame(root, background="black")

        # code for creating table
        for i in range(len(lst)):
            for j in range(len(lst[0])):
                 
                self.e = Entry(self.frame1, width=15 if j==0 else 3, fg='black',
                               font=('Arial',16))
                 
                self.e.grid(row=i, column=j)
                self.e.insert(END, lst[i][j])

  
main()
