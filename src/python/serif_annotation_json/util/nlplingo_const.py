import json
import os


def generate_nlplingo_training_parameter_str(SERIALIZATION_ROOT, nlplingo_out_path):
    json_param = {
        "trigger.restrict_none_examples_using_keywords": False,
        "data": {
            "train": {"filelist": os.path.join(SERIALIZATION_ROOT, 'argument.span_serif_list')},
            "dev": {"filelist": os.path.join(SERIALIZATION_ROOT, 'argument.span_serif_list')}
        },
        "embeddings": {
            "embedding_file": "/nfs/raid66/u14/users/jfaschin/EN-wform.w.5.cbow.neg10.400.subsmpl.txt.spaceSep.utf8",
            "missing_token": "the",
            "none_token": ".",
            "vector_size": 400,
            "vocab_size": 251236,
            "none_token_index": 0
        },
        "extractors": [
            {
                "domain_ontology": os.path.join(nlplingo_out_path, 'domain_ontology.txt'),
                "hyper-parameters": {
                    "batch_size": 100,
                    "cnn_filter_lengths": [
                        3
                    ],
                    "dropout": 0.5,
                    "entity_embedding_vector_length": 5,
                    "epoch": 10,
                    "fine-tune_epoch": 0,
                    "neighbor_distance": 3,
                    "number_of_feature_maps": 300,
                    "position_embedding_vector_length": 10,
                    "positive_weight": 10

                },
                "max_sentence_length": 201,
                "model_file": os.path.join(nlplingo_out_path, 'argument.hdf'),
                "model_flags": {
                    "use_trigger": True,
                    "use_head": True,
                    "use_event_embedding": False,
                    "train_embeddings": False
                },
                "int_type": "int32",
                "model_type": "event-argument_cnn"
            }
        ],
        "negative_trigger_words": "/nfs/raid84/u12/ychan/u40/event_type_extension/negative_words",
        "train.score_file": os.path.join(nlplingo_out_path, 'train.score'),
        "test.score_file": os.path.join(nlplingo_out_path, 'test.score'),
        "save_model": True
    }

    return json.dumps(json_param, sort_keys=True, indent=4)


Entity_type_str = """
<Entity subtype="Contact-Info">
<Entity subtype="Crime">
<Entity subtype="FAC.Airport">
<Entity subtype="FAC.Building-Grounds">
<Entity subtype="FAC.Path">
<Entity subtype="FAC.Plant">
<Entity subtype="FAC.Subarea-Facility">
<Entity subtype="GPE.Continent">
<Entity subtype="GPE.County-or-District">
<Entity subtype="GPE.GPE-Cluster">
<Entity subtype="GPE.Nation">
<Entity subtype="GPE.Population-Center">
<Entity subtype="GPE.Special">
<Entity subtype="GPE.State-or-Province">
<Entity subtype="Job-Title">
<Entity subtype="LOC.Address">
<Entity subtype="LOC.Boundary">
<Entity subtype="LOC.Celestial">
<Entity subtype="LOC.Land-Region-Natural">
<Entity subtype="LOC.Region-General">
<Entity subtype="LOC.Region-International">
<Entity subtype="LOC.Water-Body">
<Entity subtype="Numeric">
<Entity subtype="ORG.Commercial">
<Entity subtype="ORG.Educational">
<Entity subtype="ORG.Entertainment">
<Entity subtype="ORG.Government">
<Entity subtype="ORG.Media">
<Entity subtype="ORG.Medical-Science">
<Entity subtype="ORG.Non-Governmental">
<Entity subtype="ORG.Religious">
<Entity subtype="ORG.Sports">
<Entity subtype="PER.Group">
<Entity subtype="PER.Indeterminate">
<Entity subtype="PER.Individual">
<Entity subtype="Sentence">
<Entity subtype="Time">
<Entity subtype="VEH.Air">
<Entity subtype="VEH.Land">
<Entity subtype="VEH.Subarea-Vehicle">
<Entity subtype="VEH.Underspecified">
<Entity subtype="VEH.Water">
<Entity subtype="WEA.Biological">
<Entity subtype="WEA.Blunt">
<Entity subtype="WEA.Chemical">
<Entity subtype="WEA.Exploding">
<Entity subtype="WEA.Nuclear">
<Entity subtype="WEA.Projectile">
<Entity subtype="WEA.Sharp">
<Entity subtype="WEA.Shooting">
<Entity subtype="WEA.Underspecified">
<Entity subtype="ART.Oil">
<Entity subtype="ART.NaturalGas">


<Entity type="Contact-Info">
<Entity type="Crime">
<Entity type="FAC">
<Entity type="GPE">
<Entity type="Job-Title">
<Entity type="LOC">
<Entity type="OTH">
<Entity type="UNDET">
<Entity type="Numeric">
<Entity type="ORG">
<Entity type="PER">
<Entity type="Sentence">
<Entity type="Time">
<Entity type="VEH">
<Entity type="WEA">
<Entity type="HUMAN_RIGHT">
<Entity type="SEXUAL_VIOLENCE">
<Entity type="HYGIENE_TOOL">
<Entity type="FARMING_TOOL">
<Entity type="DELIVERY_KIT">
<Entity type="INSECT_CONTROL">
<Entity type="LIVESTOCK_FEED">
<Entity type="VETERINARY_SERVICE">
<Entity type="FISHING_TOOL">
<Entity type="STATIONARY">
<Entity type="TIMEX2">
<Entity type="ART">
<Entity type="FOOD">
<Entity type="LIVESTOCK">
<Entity type="MONEY">
<Entity type="SEED">
<Entity type="WATER">
<Entity type="CROP">
<Entity type="REFUGEE">
<Entity type="MEDICAL">
<Entity type="FERTILIZER">
<Entity type="THERAPEUTIC_FEEDING">
"""
