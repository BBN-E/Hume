import os, sys

hume_root = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir))

from ontology_centroid_helpers.hume_ontology.internal_ontology import build_internal_ontology_tree_without_exampler, return_node_name_joint_path_str
from ontology_centroid_helpers.external_ontology import parse_external_ontology_metadata_new


my_handmade_mapping = """
safety -> /wm/property/security
security -> /wm/property/security
biosecurity -> /wm/property/security
bio-security -> /wm/property/security
insecurity -> /wm/property/insecurity
support -> /wm/process/aid_or_assistance
[climate] change-> /wm/concept/environment/climate_change
risk -> /wm/property/risk
consumption -> /wm/process/consumption
quality -> /wm/property/quality
cases -> /wm/concept/health/case_volume
rainfall -> /wm/concept/environment/meteorology/precipitation
precipitation -> /wm/concept/environment/meteorology/precipitation
ruin -> /wm/concept/environment/meteorology/precipitation
productivity -> /wm/property/productivity
demand -> /wm/process/demand
energy -> /wm/concept/energy
adaptation -> /wm/process/adaptation
availability -> /wm/property/availability
plan -> /wm/process/planning
planning -> /wm/process/planning
disaster -> /wm/concept/crisis_or_disaster
[economic] security-> /wm/concept/security/economic_security
training -> /wm/process/training
malnutrition -> /wm/concept/health/malnutrition
emissions -> /wm/concept/environment/emissions
technology -> /wm/concept/technology
business -> /wm/concept/economy/commercial_enterprise
businesses -> /wm/concept/economy/commercial_enterprise
temperature -> /wm/concept/environment/meteorology/temperature
vulnerability -> /wm/property/vulnerability
fragility -> /wm/property/vulnerability
relief -> /wm/process/relief
harvest -> /wm/process/farming/harvesting
failure -> /wm/process/failure
failures -> /wm/process/failure
[crop] disease -> /wm/concept/agriculture/disease/crop_disease
pest -> /wm/concept/agriculture/pest
health -> /wm/concept/health
poverty -> /wm/concept/poverty
research -> /wm/process/research
availability -> /wm/property/availability
provide -> /wm/process/provision
scarce -> /wm/property/shortage
lack -> /wm/property/shortage
blight -> /wm/concept/agriculture/disease/crop_disease
destroy -> /wm/process/destruction
destroying -> /wm/process/destruction
floods -> /wm/concept/crisis_or_disaster/natural_disaster/flood
floodings -> /wm/concept/crisis_or_disaster/natural_disaster/flood
import -> /wm/process/trade/import
imports -> /wm/process/trade/import
export -> /wm/process/trade/export
exports -> /wm/process/trade/export
infection -> /wm/concept/health/disease/illness
infections -> /wm/concept/health/disease/illness
infest -> /wm/process/infestation
infests -> /wm/process/infestation
malnourished -> /wm/concept/health/malnutrition
markets -> /wm/concept/economy/commerce
marketing -> /wm/concept/economy/marketing
nutrition -> /wm/concept/health/nutrition
nutritional -> /wm/concept/health/nutrition
opposition -> /wm/process/communication/opposition
oppositions -> /wm/process/communication/opposition
pest -> /wm/concept/agriculture/pest
pests -> /wm/concept/agriculture/pest
shocks -> /wm/concept/crisis_or_disaster/shocks
shock -> /wm/concept/crisis_or_disaster/shocks
threat -> /wm/process/conflict/threat
threats -> /wm/process/conflict/threat
virus -> /wm/concept/health/pathogen
yield -> /wm/process/production
yields -> /wm/process/production
destabilize -> /wm/process/destabilization
stabilize -> /wm/process/stabilization
stabilization -> /wm/process/stabilization
instability -> /wm/property/instability
stability -> /wm/property/stability
production -> /wm/process/production
reproduction -> /wm/process/reproduction
produce -> /wm/process/production
damage -> /wm/process/damage
damages -> /wm/process/damage
pledge -> /wm/process/communication/commitment
"""

"""
[climate] change -> /Event/Environmental/Pollution/ClimateChange
[economic] security -> /Event/Compositional/EconomicSecurity, /Event/Intervention/PeaceKeepingAndSecurity/SecureLivelihoodProtections
fragility -> /Event/Compositional/Vulnerability
[crop] disease -> /Event/Agriculture/PlantDisease
scarce -> /Event/Access/WaterAccess/WaterShortage, /Event/FoodInsecurity/FoodShortage, /Event/Access/Shortage, /Event/FoodInsecurity/FoodNonaccess
destroying -> /Event/Compositional/Destruction
destroy -> /Event/Compositional/Destruction
floodings -> /Event/Environmental/Meteorologic/Weather/Flooding
infests -> /Event/CrisisAndDisaster/EnvironmentalDisasters/InsectInfestation, /Event/Agriculture/PlantDisease/PestInfestation
infest -> /Event/CrisisAndDisaster/EnvironmentalDisasters/InsectInfestation, /Event/Agriculture/PlantDisease/PestInfestation
destabilize -> /Event/Compositional/Destabilization
"""

def main():
    internal_ontology_path = os.path.join(hume_root, "resource/ontologies/internal/hume/compositional_event_ontology.yaml")
    external_ontology_path = "/nfs/raid88/u10/users/hqiu_ad/data/wm/ontology_49277ea4-7182-46d2-ba4e-87800ee5a315.yml"
    ontology_tree_root, node_name_to_nodes_mapping = build_internal_ontology_tree_without_exampler(internal_ontology_path)
    external_path_to_external_node = parse_external_ontology_metadata_new(external_ontology_path)
    external_path_to_internal_node = dict()
    for internal_node_name, internal_nodes in node_name_to_nodes_mapping.items():
        for internal_node in internal_nodes:
            for source in internal_node._source:
                if "WM:" in source:
                    external_path = source.replace("WM:","").strip()
                    if external_path in external_path_to_external_node:
                        external_path_to_internal_node.setdefault(external_path, set()).add(internal_node)
    # for external_path, internal_nodes in sorted(external_path_to_internal_node.items(), key=lambda x:len(x[1]), reverse=True):
    #     for internal_node in internal_nodes:
    #         print("{} -> {}".format(external_path, return_node_name_joint_path_str(internal_node)))
    endpoint_to_new_triggers = dict()
    for line in my_handmade_mapping.splitlines():
        line = line.strip()
        if len(line) > 0 and "->" in line:
            left,right = line.split("->")
            left = left.strip()
            right = right.strip()
            endpoint_to_new_triggers.setdefault(right, set()).add(left)
    # for endpoint, triggers in endpoint_to_new_triggers.items():
    #     if endpoint in external_path_to_internal_node:
    #         print("HIT {} -> {}".format(endpoint, ",".join(return_node_name_joint_path_str(i) for i in external_path_to_internal_node[endpoint])))
    #     else:
    #         print("MISS {}".format(endpoint))
    for endpoint, triggers in endpoint_to_new_triggers.items():
        internal_node_str = ", ".join(return_node_name_joint_path_str(internal_node) for internal_node in
                                      external_path_to_internal_node[endpoint])
        for trigger in triggers:
            print("{} -> {}".format(trigger, internal_node_str))


if __name__ == "__main__":
    main()