(test-patterns
        (AccessToHealthcare
                (toplevel
                        (event (anchor access) (regex (regex (re (text (string "food"))))))
                        (event (anchor access) (regex (regex (re (text (string "data"))))))
                        (event (anchor access) (regex (regex (re (text (string "internet"))))))
                )
        )
        (COVID-19
                (toplevel
                        (event (anchor caused))
                )
        )
	(EconomicCrisis
		(toplevel
			(event (anchor emergency) (regex (regex (re (text (string "health"))))))
			(event (anchor crisis) (regex (regex (re (text (string "health"))))))
			(event (anchor emergency) (regex (regex (re (text (string "climate"))))))
			(event (anchor crisis) (regex (regex (re (text (string "climate"))))))
			(event (anchor emergency) (regex (regex (re (text (string "political"))))))
			(event (anchor crisis) (regex (regex (re (text (string "policitcal"))))))
			(event (anchor emergency) (regex (regex (re (text (string "medical"))))))
			(event (anchor crisis) (regex (regex (re (text (string "medical"))))))
			(event (anchor hardship) (regex (regex (re (text (string "emotional"))))))
			(event (anchor recovery) (regex (regex (re (text (string "economic"))))))
		)
	)
        (EconomicGrowth
                (toplevel
                        (event (anchor growth) (regex (regex (re (text (string "population"))))))
                )
        )
        (IsolationOrConfinement
                (toplevel
                        (event (anchor -))
                        (event (anchor in))
                )
        )
        (Lockdown
                (toplevel
                        (event (anchor shut) (regex (regex (re (text (string "mouth"))))))
                )
        )
        (MaskWearing
                (toplevel
                        (event (anchor wearing) (regex (regex (re (text (string "clothes"))))))
                        (event (anchor wear) (regex (regex (re (text (string "clothes"))))))
                        (event (anchor wearing) (regex (regex (re (text (string "sunscreen"))))))
                        (event (anchor wear) (regex (regex (re (text (string "sunscreen"))))))
                        (event (anchor wearing) (regex (regex (re (text (string "jewelry"))))))
                        (event (anchor wear) (regex (regex (re (text (string "jewelry"))))))
                )
        )
        (MentalOrMood
                (toplevel
                        (event (anchor Depression) (regex (regex (re (text (string "Great"))))))
                )
        )
	(SchoolClosures
		(toplevel
			(event (anchor closure) (regex (regex (re (text (string "border"))))))
			(event (anchor closures) (regex (regex (re (text (string "border"))))))

			(event (anchor closure) (regex (regex (re (text (string "beach"))))))
			(event (anchor closures) (regex (regex (re (text (string "beach"))))))
		)
	)
	(ShortageOfFood
		(toplevel
			(event (anchor insecurity) (regex (regex (re (text (string "job"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "financial"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "income"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "housing"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "health"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "social"))))))
			(event (anchor insecurity) (regex (regex (re (text (string "(?!food$).*"))))))
			(event (anchor security) (regex (regex (re (text (string "(?!food$).*"))))))
		)
	)
	(Stay-at-homeOrder
		(toplevel
			(event (anchor order) (regex (regex (re (text (string "restraining"))))))
			(event (anchor orders) (regex (regex (re (text (string "restraining"))))))

			(event (anchor order) (regex (regex (re (text (string "emergency"))))))
			(event (anchor orders) (regex (regex (re (text (string "emergency"))))))

			(event (anchor order) (regex (regex (re (text (string "deployment"))))))
			(event (anchor orders) (regex (regex (re (text (string "deployment"))))))

			(event (anchor subscription))
			(event (anchor subscriptions))

			(event (anchor reservation))
			(event (anchor reservations))
	
			(event (anchor delivery))
			(event (anchor deliveries))

			(event (anchor scheduling))

			(event (anchor offer))
			(event (anchor offers))

			(event (anchor cancellation))
			(event (anchor cancellations))

			(event (anchor registration))
			(event (anchor registrations))

			(event (anchor lease))
			(event (anchor leasing))
		)
	)
	(Vaccination
		(toplevel
			(event (anchor assult))
        		(event (anchor overdose))	
		)
	)
        (Cause-Effect
                (toplevel
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Disease) ))
                                                    (argument (role arg2) (event (eventtype COVID-19) ))
                                        )
                        )
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Disease) ))
                                                    (argument (role arg2) (event (eventtype Virus) ))
                                        )
                        )
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Virus) ))
                                                    (argument (role arg2) (event (eventtype COVID-19) ))
                                        )
                        ) 
               )
        )
        (Precondition-Effect
                (toplevel
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Pandemic) ))
                                                    (argument (role arg2) (event (eventtype COVID-19) ))
                                        )
                        )
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Lockdown) ))
                                                    (argument (role arg2) (event (eventtype COVID-19) ))
                                        )
                        )
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Disease) ))
                                                    (argument (role arg2) (event (eventtype COVID-19) ))
                                        )
                        )
                )
        )
        (Preventative-Effect
                (toplevel
                        (event-event-relation
                                        (args
                                                    (argument (role arg1) (event (eventtype Symptom) ))
                                                    (argument (role arg2) (event (eventtype Virus) ))
                                        )
                        )
                )
        )
)
