from django.core.management.base import BaseCommand

from applications.patent_system.models import Attorney


class Command(BaseCommand):
	help = "Seed additional attorney records for patent workflow testing."

	def add_arguments(self, parser):
		parser.add_argument(
			"--count",
			type=int,
			default=4,
			help="Number of attorney records to create or update. Defaults to 4.",
		)

	def handle(self, *args, **options):
		count = max(1, min(options["count"], 4))
		attorney_specs = [
			("Attorney Alpha", "alpha.attorney@example.com", "9000000101", "Alpha IP Law", "Patentability Review"),
			("Attorney Beta", "beta.attorney@example.com", "9000000102", "Beta Legal", "Prior Art Search"),
			("Attorney Gamma", "gamma.attorney@example.com", "9000000103", "Gamma Counsel", "Drafting and Filing"),
			("Attorney Delta", "delta.attorney@example.com", "9000000104", "Delta IP Partners", "Appeals and Responses"),
		]

		created_or_updated = []
		for name, email, phone, firm_name, expertise_domain in attorney_specs[:count]:
			attorney, created = Attorney.objects.get_or_create(
				email=email,
				defaults={
					"name": name,
					"phone": phone,
					"firm_name": firm_name,
					"expertise_domain": expertise_domain,
					"is_panel_approved": True,
					"current_workload": 0,
				},
			)
			attorney.name = name
			attorney.phone = phone
			attorney.firm_name = firm_name
			attorney.expertise_domain = expertise_domain
			attorney.is_panel_approved = True
			attorney.save()
			created_or_updated.append((attorney, created))

		for attorney, created in created_or_updated:
			state = "created" if created else "updated"
			self.stdout.write(f"{attorney.name} ({attorney.email}) {state}")

		self.stdout.write(self.style.SUCCESS(f"Processed {len(created_or_updated)} attorney records."))
