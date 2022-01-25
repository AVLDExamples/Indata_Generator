import asi
from asi.ui import CompositeEditor, FormDesc, ButtonForm, StringEditor, ItemSelector, BoolEditor, IntEditor, AmountEditor
from asi import log_info, active_model
from io import StringIO
import os.path

SELECTION_NAMES = [
    "CYLINDER_PISTON_POINT",
    "CYLINDER_HEAD_POINT",
    "VALVE 0 CURTAIN_LOWER_POINT",
    "VALVE 0 CURTAIN_UPPER_POINT",
    "VALVE 0 SEAT_RING_UPPER_POINT",
    "VALVE 0 SEAT_RING_LOWER_POINT",
    "VALVE 1 CURTAIN_LOWER_POINT",
    "VALVE 1 CURTAIN_UPPER_POINT",
    "VALVE 1 SEAT_RING_UPPER_POINT",
    "VALVE 1 SEAT_RING_LOWER_POINT",
    "VALVE 2 CURTAIN_LOWER_POINT",
    "VALVE 2 CURTAIN_UPPER_POINT",
    "VALVE 2 SEAT_RING_UPPER_POINT",
    "VALVE 2 SEAT_RING_LOWER_POINT",
    "VALVE 3 CURTAIN_LOWER_POINT",
    "VALVE 3 CURTAIN_UPPER_POINT",
    "VALVE 3 SEAT_RING_UPPER_POINT",
    "VALVE 3 SEAT_RING_LOWER_POINT",
]


def _editor():

    mesh_selection =  ItemSelector(formatter = lambda x:x)

    def _add_selections(button, app, run_context):
        msh = app.Mesh.meshname
        mdl = active_model()
        meshes = [mesh for mesh in mdl.meshes if mesh.name == msh]

        if len(meshes)==1:
            mymesh = meshes[0]
            log_info('mesh found: '+msh)
            with mymesh.get_data_interface() as intf:
                existing_selections  = intf.get_node_selection_names()
                for x in SELECTION_NAMES:
                    if not x in existing_selections:
                        log_info('add '+x)
                        intf.add_node_selection(x)
                    else:
                        log_info('selection already present:'+x)

        else:
            log_info('no mesh found: '+msh)

    def _linked(editor):
        mdl = active_model()
        meshes = mdl.meshes
        meshes = [mesh for mesh in meshes if mesh.mesh.is_geometry()]
        meshnames = [mesh.name for mesh in meshes]
        if len(meshnames)>0:
            editor.subforms.button.set_enabled(True)
            editor.subforms.meshname.pool = asi.List(meshnames)
        else:
            editor.subforms.button.set_enabled(False)

    ed = CompositeEditor(
        layout = [
            #FormDesc('button', ButtonForm( labeltext="Get mesh names", action_callback=_button_pressed, width=250)),
            FormDesc( 'meshname', mesh_selection),
            FormDesc('button', ButtonForm(labeltext="Add node selection names", action_callback= _add_selections, width=250)),
            FormDesc('file_output', BoolEditor()),
            FormDesc('Ausgabe', StringEditor(singleline=False)),
            FormDesc('additional_hints', BoolEditor()),
            FormDesc('bore', AmountEditor()),
            FormDesc('intake1', IntEditor()),
            FormDesc('intake2', IntEditor()),
            FormDesc('exhaust1', IntEditor()),
            FormDesc('exhaust2', IntEditor()),
        ],
        on_target_linked = _linked
    )

    return ed

def define_app(app_desc):
    prp= app_desc.def_prop("Mesh", editor_factory=_editor)
    prp.def_slot("meshname", "tbd", pretty_name="Please enter Mesh name:")
    prp.def_slot("Ausgabe", "n/a")
    prp.def_slot("file_output", False, pretty_name="File output")
    prp.def_slot('additional_hints', False, pretty_name="Include additional hints")
    prp.def_slot("bore", (80, "length~mm"), pretty_name="Bore size")
    prp.def_slot('intake1', 0, pretty_name="Intake valve mapped to #")
    prp.def_slot('intake2', 1, pretty_name="Intake valve mapped to #")
    prp.def_slot('exhaust1', 2, pretty_name="Exhaust valve mapped to #")
    prp.def_slot('exhaust2', 3, pretty_name="Exhaust valve mapped to #")

def run_app(app):
    meshname = app.Mesh.meshname
    mdl = asi.current_model()
    m = [x for x in mdl.meshes if x.name==meshname]
    
    aus = StringIO()

    app.Mesh.Ausgabe=""

    if len(m) == 1:
        msh = m[0]

        if app.Mesh.additional_hints:
            aus.write("CYLINDER_BORE {}\n".format(app.Mesh.bore))
            aus.write("VALVE {0} TYPE INTAKE\nVALVE {1} TYPE INTAKE\nVALVE {2} TYPE EXHAUST\nVALVE {3} TYPE EXHAUST\n".format(
                app.Mesh.intake1, app.Mesh.intake2, app.Mesh.exhaust1, app.Mesh.exhaust2
            ))

        with msh.get_data_interface() as dif:
            x = dif.get_node_selection_names()
            asi.log_info("Found {} node selections:".format(len(x)))
            for sel in x:
                if sel in SELECTION_NAMES:
                    n = dif.get_num_elements_in_node_selection(sel)
                    if n>0:
                        x=dif.get_elements_in_node_selection(sel)
                        vert = dif.get_vertex(x[0])
                        print("{0} {1:.12f} {2:.12} {3:.12f}".format(sel, *vert))
                        aus.write("{0} {1:.12f} {2:.12} {3:.12f}\n".format(sel, *vert))

        if app.Mesh.file_output:
            directory = asi.current_project_location()
            if directory is not None:
                fname = meshname + ".indata"
                with open( os.path.join(directory, fname), "w") as outf:
                    outf.write(aus.getvalue())
    else:
        asi.log_info("No mesh named {} found".format(meshname))

    app.Mesh.Ausgabe=aus.getvalue()