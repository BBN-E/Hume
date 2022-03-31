(test-patterns
	(TravelRestrictions
		(toplevel
			(event 
				(anchor "旅游")
				(anchor "的")
				(anchor "行程")
				(anchor "预订")
				(anchor "补贴")
				(anchor "生活")
				(anchor "交通")
				(anchor "禁行")
			)
		)
	)
	(COVID-19
		(toplevel
		        (event (anchor "的"))
		        (event (anchor "冠"))
		        (event (anchor "冠状"))
		        (event (anchor "冠病"))
			(event (anchor "冠肺"))
		)
	)
	(MaskWearing
		(toplevel
		        (event (anchor "，"))
		        (event (anchor "穿"))
			(event (anchor "佩戴") (regex (regex (re (text (string "头盔"))))) )
			(event (anchor "戴") (regex (regex (re (text (string "头盔"))))) )
			(event (anchor "戴上") (regex (regex (re (text (string "头盔"))))) )
			(event (anchor "打响"))
			(event (anchor "都"))
			(event (anchor "生"))
			(event (anchor "身穿"))
			(event (anchor "使用"))
			(event (anchor "、"))
			(event (anchor "回穿"))
		)
	)
	(PersonalBehaviors
		(toplevel
			(event (anchor "的"))

		)
	)
	(Transmission
		(toplevel
			(event (anchor "传输"))
			(event (anchor "的"))
		)
	)
	(Employment
		(toplevel
			(event (anchor "就"))
			(event (anchor "、"))
			(event (anchor "稳就"))
		)
	)
	(Shortage
		(toplevel
			(event (anchor "短板"))
		)
	)
	(Stay-at-homeOrder
		(toplevel
			(event (anchor "订单"))
			(event (anchor "登记"))
			(event (anchor "让"))
			(event (anchor "办理"))
			(event (anchor "申请"))
			(event (anchor "订购"))
			(event (anchor "令"))
			(event (anchor "单"))
			(event (anchor "宿订"))
			(event (anchor "预约"))
			(event (anchor "办贷"))
			(event (anchor "登記"))
			(event (anchor "領用"))
			(event (anchor "单"))
			(event (anchor "级 订"))
			(event (anchor "手订"))
		)
	)
	(SocialDistancing
		(toplevel
			(event (anchor "秩序"))
			(event (anchor "分化"))
			(event (anchor "不"))
			(event (anchor "稳定"))
			(event (anchor "脱"))
			(event (anchor "的"))
		)
	)
	(IsolationOrConfinement
		(toplevel
			(event (anchor "在"))
			(event (anchor "登记"))
			(event (anchor "，"))
			(event (anchor "的"))
			(event (anchor "、"))
		)
	)
	(Virus
		(toplevel
			(event (anchor "这"))
			
		)
	)
	(Treatment
		(toplevel
			(event (anchor "的"))
			(event (anchor "服务"))
			
		)
	)
	(Inflation
		(toplevel
			(event (anchor "降费"))
		)
	)
	(ShortageOfFood
		(toplevel
			(event (anchor "安全"))
		)
	)
	(MentalOrMood
		(toplevel
			(event (anchor "、"))
			(event (anchor "的"))
		)
	)
	(Disease
		(toplevel
			(event (anchor "性"))
			(event (anchor "的"))
		)
	)
	(HandWashing
		(toplevel
			(event (anchor "手卫"))
			(event (anchor "着"))
			(event (anchor "手安"))
			(event (anchor "手持"))
			(event (anchor "手"))
			(event (anchor "手持"))
			(event (anchor "东西手拉"))
			(event (anchor "洗碗"))
			(event (anchor "手边"))
			(event (anchor "祭扫"))
			(event (anchor "修路"))
			(event (anchor "接手"))
			(event (anchor "清洁"))
			(event (anchor "整理"))
			(event (anchor "生"))
			(event (anchor "洗礼"))
			(event (anchor "整潔"))
			(event (anchor "洗碗"))
		)
	)
	(Death
		(toplevel
			(event (anchor "和"))
			(event (anchor "例"))

		)
	)
	(SchoolClosures
		(toplevel
			(event (anchor "停工"))
		)
	)
	(Protest
		(toplevel
			(event (anchor "镇压"))
		)
	)
	(Pandemic
		(toplevel
			(event (anchor "大"))
		)
	)
)
