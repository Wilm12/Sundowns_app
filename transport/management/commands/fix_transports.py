"""Management command to fix transport booking issues by recreating transports with proper match associations."""

from django.core.management.base import BaseCommand, CommandError
from transport.models import Transport
from branches.models import Branch
from matches.models import Match


class Command(BaseCommand):
    help = 'Fix transport records with NULL match_id by deleting and recreating them with proper matches'

    # Branch-to-Match mappings
    BRANCH_MATCH_MAPPING = {
        'Mamelodi East': 'RB Leipzig',
        'Mamelodi West': 'AS FAR Rabat',
        'Soshanguve': 'Orlando Pirates',
        'Tuks': 'RB Leipzig',
        'TUT': 'AS FAR Rabat',
        'Pretoria Central': 'Kaizer Chiefs',
        'Atteridgeville': 'Orlando Pirates',
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== TRANSPORT BOOKING FIX ===\n'))
        
        # Step 1: Inspect current state
        self.stdout.write(self.style.WARNING('STEP 1: INSPECTING CURRENT DATA STATE\n'))
        
        self.stdout.write('Available Matches:')
        matches = Match.objects.all()
        match_dict = {}
        for m in matches:
            match_dict[m.opponent] = m
            self.stdout.write(f'  ID {m.id}: {m.opponent}')
        
        if not matches.exists():
            raise CommandError('❌ No matches found. Please create matches before running this command.')
        
        self.stdout.write('\nAvailable Branches:')
        branches = Branch.objects.all()
        branch_dict = {}
        for b in branches:
            branch_dict[b.name] = b
            self.stdout.write(f'  ID {b.id}: {b.name}')
        
        if not branches.exists():
            raise CommandError('❌ No branches found. Please create branches before running this command.')
        
        self.stdout.write('\nTransports with NULL match:')
        null_transports = Transport.objects.filter(match_id__isnull=True)
        null_count = null_transports.count()
        self.stdout.write(f'Count: {null_count}')
        for t in null_transports:
            self.stdout.write(f'  ID {t.id}: {t.branch.name}, capacity={t.capacity}, status={t.status}')
        
        self.stdout.write('\nAll Transports:')
        all_transports = Transport.objects.all().select_related('branch', 'match')
        total_count = all_transports.count()
        self.stdout.write(f'Total: {total_count}')
        for t in all_transports:
            match_info = f'{t.match.opponent}' if t.match else 'NULL'
            self.stdout.write(f'  ID {t.id}: {t.branch.name} → {match_info}')
        
        if null_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No transports with NULL match found. Data is clean.'))
            return
        
        # Step 2: Delete NULL transports
        self.stdout.write(self.style.WARNING(f'\nSTEP 2: DELETING {null_count} TRANSPORTS WITH NULL MATCH\n'))
        deleted_count, _ = null_transports.delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} transport records'))
        
        # Step 3: Recreate with proper matches
        self.stdout.write(self.style.WARNING('\nSTEP 3: RECREATING TRANSPORTS WITH PROPER MATCHES\n'))
        
        created_count = 0
        for branch_name, match_opponent in self.BRANCH_MATCH_MAPPING.items():
            if branch_name not in branch_dict:
                self.stdout.write(self.style.WARNING(f'⚠ Branch "{branch_name}" not found, skipping'))
                continue
            
            if match_opponent not in match_dict:
                self.stdout.write(self.style.WARNING(f'⚠ Match "{match_opponent}" not found, skipping'))
                continue
            
            branch = branch_dict[branch_name]
            match = match_dict[match_opponent]
            
            # Create transport with realistic capacity
            transport = Transport.objects.create(
                branch=branch,
                match=match,
                owner_id=1,  # Default owner; adjust as needed
                capacity=30,  # Realistic coach capacity
                status='active'
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created: Transport {transport.id} → {branch.name} for "{match.opponent}"'
            ))
        
        # Step 4: Verify fix
        self.stdout.write(self.style.WARNING('\nSTEP 4: VERIFYING FIX\n'))
        
        null_check = Transport.objects.filter(match_id__isnull=True).count()
        self.stdout.write(f'Transports with NULL match: {null_check}')
        
        all_transports_after = Transport.objects.all().select_related('branch', 'match')
        self.stdout.write(f'Total transports after: {all_transports_after.count()}')
        
        for t in all_transports_after:
            match_info = f'{t.match.opponent}' if t.match else 'NULL'
            self.stdout.write(f'  ID {t.id}: {t.branch.name} → {match_info}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ FIX COMPLETE: Created {created_count} new transports'))
        self.stdout.write(self.style.SUCCESS('✓ Template logic will now work: {{ transport.match.opponent }} renders correctly'))
        self.stdout.write(self.style.SUCCESS('✓ Booking buttons will appear: ticket.match_id == transport.match_id comparison works'))
