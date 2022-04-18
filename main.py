
# importing the tkinter module and PIL
# that is pillow module
from cProfile import label
import copy
from genericpath import exists
import glob
import json
import math
from tkinter import *
from PIL import ImageTk, Image


def reset_state_full():
    global state
    global canvas

    state = copy.deepcopy(state_default)
    # delete all the lines
    canvas.delete('line')
    canvas.delete('circle')
    canvas.delete('bisector_circle')
    canvas.delete('tmp_bisector_circle')
    for state_class in state['classes'][1:]:
        canvas.delete(state_class['name'])

def reset_state_part():
    global state
    global canvas

    for i, state_class in enumerate(state['classes']):
        if state_class['name'] == state['active_class']:
            if state_class['name'] != 'gonion':
                canvas.delete(state_class['name'])
            else:
                canvas.delete('line')
                canvas.delete('circle')
                canvas.delete('bisector_circle')
                canvas.delete('tmp_bisector_circle')
            state_class= copy.deepcopy(state_default['classes'][i])
            state['classes'][i] = state_class
def create_circle(canvasName,x, y, r=3,tag = 'circle',color = 'black'): #center coordinates, radius
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvasName.create_oval(x0, y0, x1, y1,tag = tag,fill = color)

def create_line(canvas,x_1, y_1, x_2, y_2,color='yellow',width=2):
    # use equation of a line to extend the line to the end of the canvas, while maintaining the same slope
    m = (y_2 - y_1) / (x_2 - x_1)
    b = y_1 - m * x_1
    x_end = canvas.winfo_width()
    y_end = m * x_end + b
    x_start = 0
    y_start = m * x_start + b
    canvas.create_line(x_start, y_start, x_end, y_end,width=width,fill=color,tag='line')

def on_button_1_clicked(tk_event):
    global state
    global canvas

    # print("Button 1 clicked",tk_event)
    if state['active_class'] == 'gonion':
        state_gonion = state['classes'][0]
        if state_gonion['first_line'] == False:
            state_gonion['first_line'] = [tk_event]
            create_circle(canvas,tk_event.x,tk_event.y)
            print("First line")
        elif len(state_gonion['first_line']) == 1:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['first_line'] = [state_gonion['first_line'][0], tk_event]
            create_line(canvas, state_gonion['first_line'][0].x, state_gonion['first_line'][0].y, tk_event.x, tk_event.y)
            print("First line")
        elif state_gonion['second_line'] == False:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['second_line'] = [tk_event]
            print("Second line")
        elif len(state_gonion['second_line']) == 1:
            create_circle(canvas,tk_event.x,tk_event.y)
            state_gonion['second_line'] = [state_gonion['second_line'][0], tk_event]
            print("Second line")
            create_line(canvas, state_gonion['second_line'][0].x, state_gonion['second_line'][0].y, tk_event.x, tk_event.y)
            create_angle_bisector(canvas)
        elif state_gonion['third_mouse_click'] == False:

            state_gonion['third_mouse_click'] = tk_event
            x,y,c =  state_gonion['bisector']
            x_pos,y_pos = get_circle_loc_on_bisector(tk_event, x, y, c)
            create_circle(canvas,x_pos,y_pos,r=2,tag='bisector_circle',color='yellow')
            state_gonion['bisector'] = False
            print("Third line")
        state['classes'][0] = state_gonion
    else:
        for state_class in state['classes']:
            if state_class['name'] == state['active_class']:
                state_class['pos'] = tk_event
                canvas.delete(state_class['name'])
                create_circle(canvas,tk_event.x,tk_event.y,tag=state_class['name'],color=state_class['color'])
                state['classes'][state['classes'].index(state_class)] = state_class
                break

def create_angle_bisector(canvas):
    global state
    state_gonion = state['classes'][0]
    first_line = state_gonion['first_line']
    second_line = state_gonion['second_line']
    x, y, c = get_line_bisector_params(first_line, second_line,-1)
    m = x/y
    if m<0:
        x, y, c = get_line_bisector_params(first_line, second_line,1)
    x_intercept = -c/x
    y_intercept = -c/y
    state_gonion['bisector'] = [x,y,c]
    create_line(canvas, 0, y_intercept,x_intercept, 0,color='red',width=1)
    state['classes'][0] = state_gonion

def get_line_bisector_params(first_line, second_line,multiplier=1):
    a1, b1, c1  = get_line_equation(first_line[0].x, first_line[0].y, first_line[1].x, first_line[1].y)
    a2, b2, c2  = get_line_equation(second_line[0].x, second_line[0].y, second_line[1].x, second_line[1].y)
    right_term = multiplier*math.sqrt(a1**2 + b1**2)/math.sqrt(a2**2 + b2**2)
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
    if state_gonion['bisector']!=False:
        x,y,c = state_gonion['bisector']
        event_x, y_pos = get_circle_loc_on_bisector(event, x, y, c)
        canvas.delete('tmp_bisector_circle')
        create_circle(canvas,event_x,y_pos,r=2,tag='tmp_bisector_circle')


def get_circle_loc_on_bisector(event, x, y, c):
    event_x = event.x
    y_pos = -(event_x*x + c)/y
    return event_x,y_pos

def create_canvas(image):
    global root
    canvas = Canvas(root, width=MAX_SIZE, height =MAX_SIZE )
    # We have to show the the box so this below line is needed

    canvas.create_image(10, 10, anchor=NW, image=image)
    canvas.grid(row=1, column=0, columnspan=4)
    canvas.bind("<Button-1>", on_button_1_clicked)
    canvas.bind('<Motion>', draw_hover_circle)
    canvas.bind('<Enter>', draw_hover_circle) 
    root.bind('<Key>', key_pressed)
    return canvas

def key_pressed(event):
    global state
    global label_active_class
    if event.char == 'r':
        reset_state_full()
        return
    try:
        if int(event.char) in list(range(1,len(state['classes'])+1)):
            state['active_class'] = state['classes'][int(event.char)-1]['name']
            print(state['active_class'])
        label_active_class.config(text=f"Active class: {state['active_class']}")
        active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
        label_active_class.config(fg=active_class['color'])
    except ValueError as e:
        print(e)
    return


def forward(img_path):
    global canvas
    global button_forward
    global button_back
    global button_clear
    global state
    global img_paths
    global label_active_class

    canvas.grid_forget()
    reset_state_full()
 

    canvas = create_canvas(create_image_from_path(img_path))

    create_forward_button(img_path)
 

    button_back = Button(root, text="Back",
                         command=lambda: back(img_paths[img_paths.index(img_path)-1]))
    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'])

    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)

def create_forward_button(img_path):
    global button_forward
    if img_paths.index(img_path) == len(img_paths)-1:
        button_forward = Button(root, text="Forward",
                                state=DISABLED)
    else:
        button_forward = Button(root, text="forward",
                        command=lambda: forward(img_paths[img_paths.index(img_path)+1]))
 
def back(img_path):

    global canvas
    global button_forward
    global button_back
    global button_clear
    global label_active_class
    global state
    global img_paths

    canvas.grid_forget()
    reset_state_full()

    # for clearing the image for new image to pop up
    canvas = create_canvas(create_image_from_path(img_path))

    button_forward = Button(root, text="forward",
                            command=lambda: forward(img_paths[img_paths.index(img_path)+1]))
    print(img_path)

    create_back_button(img_path)
        
    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'])

    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)

def create_back_button(img_path):
    global button_back
    if img_paths.index(img_path) == 0:
        button_back = Button(root, text="Back", state=DISABLED)
    else:
        button_back = Button(root, text="Back",command=lambda: back(img_paths[img_paths.index(img_path)-1]))
    
 

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

    img_paths = glob.glob("images/*.jpg")

    if exists('db.json'):
        with open('db.json', 'r') as f:
            db = json.load(f)
    else:
        db = {
            "current_image":img_paths[0],
            "data":{

            }
        }
    current_image = db['current_image']

    canvas = create_canvas(create_image_from_path(current_image))

    reset_state_full()


    button_back = Button(root, text="Back", command=back,
                     state=DISABLED)
 
    button_clear = Button(root, text="Clear", command=reset_state_part)
 
    button_forward = Button(root, text="Forward",
                        command=lambda: forward(img_paths[img_paths.index(current_image)+1]))

    active_class = [state_class for state_class in state['classes'] if state_class['name'] == state['active_class']][0]
    label_active_class = Label(root, text=f"Active Class: {state['active_class']}",fg=active_class['color'])
 
    button_back.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    label_active_class.grid(row=5, column=3)
 
    root.mainloop()

def create_image_from_path(image):
    pil_im = Image.open(image)
    pil_im = pil_im.resize((MAX_SIZE, MAX_SIZE), Image.ANTIALIAS)
    im =ImageTk.PhotoImage(pil_im)
    return im

MAX_SIZE = 900

state_default = {
    'active_class': 'gonion',
    'classes':[
        {
            'name': 'gonion',
            "first_line": False,
            "second_line": False,
            "third_mouse_click": False,
            "bisector":False,
            'color': 'orange'
        },
        {
            'name': 'second_class',
            'color': 'blue', 
            'pos':False
        },
        {
            'name': 'third_class',
            'color': 'green',
            'pos':False
        },
        {
            'name': 'fourth_class',
            'color': 'red',
            'pos':False
        }
    ]
}
main()
