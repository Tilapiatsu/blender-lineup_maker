import bpy


def get_layer_collection(layer_collection, collection_name):
    found = None
    if (layer_collection.name == collection_name):
        return layer_collection
    for layer in layer_collection.children:
        found = get_layer_collection(layer, collection_name)
        if found:
            return found

def create_asset_collection(context, name):
    collections = bpy.data.collections
    if name in collections:
        return collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        context.collection.children.link(new_collection)
        return new_collection


def set_active_collection(context, name):
    context.view_layer.active_layer_collection = get_layer_collection(context.view_layer.layer_collection, name)
    