# Annotation

Will become central piece of exchanging all annotation in CauseEx/WM group.

# Data structure

```json
{
	"docid": "ENG_XXX", 
	"event_mentions": [
		{
			"types": [
				{
					"source": "LearnIt/candidates"
					"type" : [
						["DefenseOrSupport", True], 
						["DefensiveManeuver, True]
					]
				},
				{
					"source": "AMT/A20NITCOBY4775", 
					"type" : [
						["DefenseOrSupport", True]
						["Decision", True]
					]
				}, 
				{
					"source": "AMT/A2UF2FRGVW4T89"
					"type" : [
						["NA", True]
					]
				}, 
				{
					"source": "NLPLINGO"
					"type" : [
						["DefenseOrSupport", True]
					]
				}, 
				{
					"source": "LearnIt/HAT"
					"type" : [
						["DefenseOrSupport", True]
					]
				}
			], 
			"trigger": {
				"span": {
					"char_start": 1237, 
					"char_end", 1244
				}, 
				"text": "", 
				"normalized_text": ""
			}
			"sentence": {
				"span": {
					"char_start": 1232, 
					"char_end": 1381
				}, 
				"text": ""
			}
			"arguments": [
				{
					"source": "LearnIt/candidate"
					"role": [
						["has_affected_actor", True]
						["has_active_actor", True]
					],
					"span": {
						"char_start": 1232, 
						"char_end": 1235
					}
					"type": "ORG", 
				},
				{
					"source": "AMT/A20NITCOBY4775"
					"role":  [
						["has_affected_actor", True]
					],
					"span": {
						"char_start": 1232, 
						"char_end": 1235
					}
					"type": "GPE", 
				}
			]
		}
	], 
	"relation_mentions": [
		{
			"types": [
				{
					"source": "LearnIt/candidates"
					"type" : [
						["Cause-Effect", True], 
						["Before-After, True]
					]
				},
				{
					"source": "AMT/A20NITCOBY4775", 
					"type" : [
						["Cause-Effect", True]
					]
				}, 
				{
					"source": "AMT/A2UF2FRGVW4T89"
					"type" : [
						["NA", True]
					]
				}, 
				{
					"source": "LearnIt/pattern"
					"type" : [
						["Before-After", True]
					]
				}, 
				{
					"source": "LearnIt/HAT"
					"type" : [
						["Before-After", True]
					]
				}
			], 
			"trigger": {
				"span": {
					"char_start": 1237, 
					"char_end", 1244
				}, 
				"text": "", 
			}
			"arguments": [
				{
					"role": "arg1",
					"span": {
						"char_start": 1232, 
						"char_end": 1235
					},
					"text": "clash",
					"type": "Conflict", 
					"sentence": {
						"span": {
							"char_start": 1232, 
							"char_end": 1381
						}, 
						"text": ""
					}, 
					"properties": {
						"id": "Generic|PER [stay]",
						"word": "stay"
					}
				},
				{
					"role":  "arg2",
					"span": {
						"char_start": 1232, 
						"char_end": 1235
					}, 
					"text": "clash",
					"type": "Event", 
					"sentence": {
						"span": {
							"char_start": 1232, 
							"char_end": 1381
						}, 
						"text": ""
					}, 
					"properties": {
						"id": "Generic|PER [stay]",
						"word": "stay"
					}
				}
			]
		}
	], 
} 
```