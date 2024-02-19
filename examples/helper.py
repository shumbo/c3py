from IPython.display import Image, display


def view_pydot(G):
    plt = Image(G.create_png())
    display(plt)
