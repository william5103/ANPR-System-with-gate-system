import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import firestore as firestore_types
import datetime


class FirebaseDB:
    def __init__(self, credentials_path):
        try:
            # Initialize Firebase app
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            
            # Initialize Firestore client
            self.db = firestore.client()
            print("Firebase connection established successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
    
    # Owner
    def add_owner(self, owner_name, owner_ic, owner_identity, owner_id, owner_phone, owner_email, vehicle_plate, entry_reason, brand=None, model=None, admin_id=None):
        try:
            # Calculate expiry date
            expiry_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Create data dictionary
            data = {
                'owner_name': owner_name,
                'owner_ic': owner_ic,
                'owner_identity': owner_identity,
                'owner_id': owner_id,
                'owner_phone': owner_phone,
                'owner_email': owner_email,
                'vehicle_plate': vehicle_plate,
                'entry_reason': entry_reason,
                'status': 'Active',
                'expiry_date': expiry_date,
                'created_at': firestore_types.SERVER_TIMESTAMP
            }
            if brand:
                data['brand'] = brand
            if model:
                data['model'] = model
            
            # Add to owners collection
            doc_ref = self.db.collection('owners').document(owner_id)
            doc_ref.set(data)
            
            print(f"Owner {owner_name} added with ID: {owner_id}")
            if admin_id:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Added owner",
                    target_type="owner",
                    target_id=owner_id,
                    details=data
                )
            return owner_id
        except Exception as e:
            print(f"Error adding owner: {e}")
            return None

    def get_owners(self, limit=100):
        try:
            # Query the collection
            records_ref = self.db.collection('owners')
            query = records_ref.order_by('created_at', direction=firestore_types.Query.DESCENDING).limit(limit)
            docs = query.stream()

            # Process results
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)

            return results
        except Exception as e:
            print(f"Error retrieving records: {e}")
            return []

    def get_owner(self, owner_id):
        try:
            doc_ref = self.db.collection('owners').document(owner_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                print(f"Owner with ID {owner_id} not found.")
                return None
        except Exception as e:
            print(f"Error retrieving owner: {e}")
            return None
    
    def update_owner(self, owner_id, owner_name=None, owner_ic=None, owner_identity=None, owner_phone=None, owner_email=None, vehicle_plate=None, entry_reason=None, status=None, expiry_date=None, brand=None, model=None, admin_id=None):
        try:
            # Create update data dictionary
            update_data = {}
            if owner_name is not None:
                update_data['owner_name'] = owner_name
            if owner_ic is not None:
                update_data['owner_ic'] = owner_ic
            if owner_identity is not None:
                update_data['owner_identity'] = owner_identity
            if owner_phone is not None:
                update_data['owner_phone'] = owner_phone
            if owner_email is not None:
                update_data['owner_email'] = owner_email
            if vehicle_plate is not None:
                update_data['vehicle_plate'] = vehicle_plate
            if entry_reason is not None:
                update_data['entry_reason'] = entry_reason
            if status is not None:
                update_data['status'] = status
            if expiry_date is not None:
                update_data['expiry_date'] = expiry_date
            if brand is not None:
                update_data['brand'] = brand
            if model is not None:
                update_data['model'] = model
            
            # Add update timestamp
            update_data['updated_at'] = firestore_types.SERVER_TIMESTAMP
            
            # Update the document
            doc_ref = self.db.collection('owners').document(owner_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.update(update_data)
            
            print(f"Owner with ID {owner_id} updated successfully.")
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Updated owner",
                    target_type="owner",
                    target_id=owner_id,
                    details={"before": before, "after": update_data}
                )
            return True
        except Exception as e:
            print(f"Error updating owner: {e}")
            return False
    
    def delete_owner(self, owner_id, admin_id=None):
        try:
            doc_ref = self.db.collection('owners').document(owner_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.delete()
            
            print(f"Owner with ID {owner_id} deleted successfully.")
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Deleted owner",
                    target_type="owner",
                    target_id=owner_id,
                    details=before
                )
            return True
        except Exception as e:
            print(f"Error deleting owner: {e}")
            return False
    
    def search_owners(self, field, value):
        try:
            owners_ref = self.db.collection('owners')
            query = owners_ref.where(field, '==', value)
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error searching owners: {e}")
            return []
    
    # Admin
    def add_admin(self, admin_id, admin_name, admin_ic, admin_address, admin_phone, admin_email, admin_password, performed_by=None):
        try:
            # Create data dictionary
            data = {
                'admin_id': admin_id,
                'admin_name': admin_name,
                'admin_ic': admin_ic,
                'admin_address': admin_address,
                'admin_phone': admin_phone,
                'admin_email': admin_email,
                'admin_password': admin_password,
                'created_at': firestore_types.SERVER_TIMESTAMP
            }
            
            # Add to admins collection
            doc_ref = self.db.collection('admins').document(admin_id)
            doc_ref.set(data)
            
            print(f"Admin {admin_name} added with ID: {admin_id}")
            if performed_by:
                # Create a copy of data without password for logging
                log_data = data.copy()
                del log_data['admin_password']
                del log_data['created_at']
                
                self.add_admin_action(
                    admin_id=performed_by,
                    action="Added admin",
                    target_type="admin",
                    target_id=admin_id,
                    details=log_data
                )
            return admin_id
        except Exception as e:
            print(f"Error adding admin: {e}")
            return None
    
    def get_admins(self, limit=100):
        try:
            # Query the collection
            admins_ref = self.db.collection('admins')
            query = admins_ref.order_by('created_at', direction=firestore_types.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            # Process results
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error retrieving admins: {e}")
            return []

    def get_admin(self, admin_id):
        try:
            query = self.db.collection('admins').where('admin_id', '==', admin_id).limit(1).stream()
            for doc in query:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error retrieving admin: {e}")
            return None

    def update_admin(self, admin_id, update_data, performed_by=None):
        try:
            # Add update timestamp
            update_data['updated_at'] = firestore_types.SERVER_TIMESTAMP
            
            # Check if password is being updated
            is_password_update = 'admin_password' in update_data and update_data['admin_password']
            
            # Update the document
            doc_ref = self.db.collection('admins').document(admin_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.update(update_data)
            
            print(f"Admin with ID {admin_id} updated successfully.")
            if performed_by and before:
                # Remove password and timestamps from before data
                before_log = before.copy()
                if 'admin_password' in before_log:
                    del before_log['admin_password']
                if 'created_at' in before_log:
                    del before_log['created_at']
                if 'updated_at' in before_log:
                    del before_log['updated_at']
                
                # Remove password and timestamps from after data
                after_log = update_data.copy()
                if 'admin_password' in after_log:
                    del after_log['admin_password']
                if 'updated_at' in after_log:
                    del after_log['updated_at']
                
                # Set action based on whether password was updated
                action = "Update admin with password" if is_password_update else "Update admin"
                
                self.add_admin_action(
                    admin_id=performed_by,
                    action=action,
                    target_type="admin",
                    target_id=admin_id,
                    details={"before": before_log, "after": after_log}
                )
            return True
        except Exception as e:
            print(f"Error updating admin: {e}")
            return False
    
    def delete_admin(self, admin_id, performed_by=None):
        try:
            doc_ref = self.db.collection('admins').document(admin_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.delete()
            
            print(f"Admin with ID {admin_id} deleted successfully.")
            if performed_by and before:
                self.add_admin_action(
                    admin_id=performed_by,
                    action="Deleted admin",
                    target_type="admin",
                    target_id=admin_id,
                    details=before
                )
            return True
        except Exception as e:
            print(f"Error deleting admin: {e}")
            return False
    
    # Security
    def add_security(self, security_id, security_name, security_ic, security_email, security_phone, security_address, security_password, admin_id=None):
        try:
            # Store password as plain text (for debugging only)
            data = {
                'security_id': security_id,
                'security_name': security_name,
                'security_ic': security_ic,
                'security_email': security_email,
                'security_phone': security_phone,
                'security_address': security_address,
                'security_password': security_password,
                'created_at': firestore_types.SERVER_TIMESTAMP
            }
            # Add to security collection
            doc_ref = self.db.collection('security').document(security_id)
            doc_ref.set(data)
            print(f"Security personnel {security_name} added with ID: {security_id}")
            
            # Create a copy of data without password for logging
            log_data = data.copy()
            del log_data['security_password']
            del log_data['created_at']
            
            if admin_id:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Added security",
                    target_type="security",
                    target_id=security_id,
                    details=log_data
                )
            return security_id
        except Exception as e:
            print(f"Error adding security personnel: {e}")
            return None
    
    def get_security_personnel(self, limit=100):
        try:
            # Query the collection
            security_ref = self.db.collection('security')
            query = security_ref.order_by('created_at', direction=firestore_types.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            # Process results
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error retrieving security personnel: {e}")
            return []

    def get_security_person(self, security_id):
        try:
            query = self.db.collection('security').where('security_id', '==', security_id).limit(1).stream()
            for doc in query:
                return doc.to_dict()
            print(f"Security personnel with ID {security_id} not found.")
            return None
        except Exception as e:
            print(f"Error retrieving security personnel: {e}")
            return None

    def update_security(self, security_id, update_data, admin_id=None):
        try:
            # Add update timestamp
            update_data['updated_at'] = firestore_types.SERVER_TIMESTAMP
            
            # Check if password is being updated
            is_password_update = 'security_password' in update_data and update_data['security_password']
            
            # Update the document
            doc_ref = self.db.collection('security').document(security_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.update(update_data)
            print(f"Security personnel with ID {security_id} updated successfully.")
            
            if admin_id and before:
                # Remove password and timestamps from before data
                before_log = before.copy()
                if 'security_password' in before_log:
                    del before_log['security_password']
                if 'created_at' in before_log:
                    del before_log['created_at']
                if 'updated_at' in before_log:
                    del before_log['updated_at']
                
                # Remove password and timestamps from after data
                after_log = update_data.copy()
                if 'security_password' in after_log:
                    del after_log['security_password']
                if 'updated_at' in after_log:
                    del after_log['updated_at']
                
                # Set action based on whether password was updated
                action = "Update security with password" if is_password_update else "Update security"
                
                self.add_admin_action(
                    admin_id=admin_id,
                    action=action,
                    target_type="security",
                    target_id=security_id,
                    details={"before": before_log, "after": after_log}
                )
            return True
        except Exception as e:
            print(f"Error updating security personnel: {e}")
            return False
    
    def delete_security(self, security_id, admin_id=None):
        try:
            doc_ref = self.db.collection('security').document(security_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.delete()
            
            print(f"Security personnel with ID {security_id} deleted successfully.")
            if admin_id and before:
                # Remove password and timestamps from log data
                log_data = before.copy()
                if 'security_password' in log_data:
                    del log_data['security_password']
                if 'created_at' in log_data:
                    del log_data['created_at']
                if 'updated_at' in log_data:
                    del log_data['updated_at']
                
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Deleted security",
                    target_type="security",
                    target_id=security_id,
                    details=log_data
                )
            return True
        except Exception as e:
            print(f"Error deleting security personnel: {e}")
            return False
    
    # Records
    def add_record(
        self,
        vehicle_plate,
        owner_identity,
        owner_phone,
        entry_date,
        entry_time,
        entry_reason,
        owner_id=None,
        exit_date=None,
        exit_time=None,
        record_id=None,
        owner_name=None,
        owner_ic=None,
        brand=None,
        model=None,
        admin_id=None,
        security_id=None
    ):
        try:
            if not record_id:
                # Scan all records to find the max record_id number
                records_ref = self.db.collection('records')
                docs = records_ref.stream()
                max_number = 0
                for doc in docs:
                    data = doc.to_dict()
                    rec_id = data.get('record_id', '')
                    if rec_id.startswith('REC'):
                        try:
                            num = int(rec_id.replace('REC', ''))
                            if num > max_number:
                                max_number = num
                        except ValueError:
                            continue
                next_number = max_number + 1
                record_id = f'REC{next_number}'


            if owner_identity in ['student', 'staff'] and not owner_id:
                print("owner_id is required for students and staff.")
                return None

            # Create data dictionary
            data = {
                'record_id': record_id,
                'vehicle_plate': vehicle_plate,
                'owner_identity': owner_identity,
                'owner_phone': owner_phone,
                'entry_date': entry_date,
                'entry_time': entry_time,
                'entry_reason': entry_reason,
                'created_at': firestore_types.SERVER_TIMESTAMP
            }
            
            # Add owner information
            if owner_identity in ['student', 'staff']:
                data['owner_id'] = owner_id
            if owner_name:
                data['owner_name'] = owner_name
            if owner_ic:
                data['owner_ic'] = owner_ic
            if exit_date:
                data['exit_date'] = exit_date
            if exit_time:
                data['exit_time'] = exit_time
            if brand:
                data['brand'] = brand
            if model:
                data['model'] = model

            # Add to records collection
            doc_ref = self.db.collection('records').document(record_id)
            doc_ref.set(data)

            print(f"Record added with ID: {record_id}")
            if admin_id:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Added record",
                    target_type="record",
                    target_id=record_id,
                    details=data
                )
            elif security_id:
                self.add_security_action(
                    security_id=security_id,
                    action="Added record",
                    target_type="record",
                    target_id=record_id,
                    details=data
                )
            return record_id
        except Exception as e:
            print(f"Error adding record: {e}")
            return None
    
    def get_records(self, limit=100):
        try:
            # Query the collection
            records_ref = self.db.collection('records')
            query = records_ref.order_by('created_at', direction=firestore_types.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            # Process results
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error retrieving records: {e}")
            return []
    
    def get_record(self, record_id):
        try:
            doc_ref = self.db.collection('records').document(record_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                print(f"Record with ID {record_id} not found.")
                return None
        except Exception as e:
            print(f"Error retrieving record: {e}")
            return None
    
    def update_record(self, record_id, update_data, admin_id=None, security_id=None):
        try:
            # Retrieve the existing record to get current values
            doc_ref = self.db.collection('records').document(record_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None

            # Required fields
            vehicle_plate = update_data.get('vehicle_plate', before.get('vehicle_plate'))
            owner_identity = update_data.get('owner_identity', before.get('owner_identity'))
            owner_phone = update_data.get('owner_phone', before.get('owner_phone'))
            entry_date = update_data.get('entry_date', before.get('entry_date'))
            entry_time = update_data.get('entry_time', before.get('entry_time'))
            entry_reason = update_data.get('entry_reason', before.get('entry_reason'))

            # owner_id is required for student/staff
            owner_id = update_data.get('owner_id', before.get('owner_id'))
            if owner_identity in ['student', 'staff'] and not owner_id:
                print("owner_id is required for students and staff.")
                return False

            # Optional fields
            exit_date = update_data.get('exit_date', before.get('exit_date'))
            exit_time = update_data.get('exit_time', before.get('exit_time'))
            owner_name = update_data.get('owner_name', before.get('owner_name'))
            owner_ic = update_data.get('owner_ic', before.get('owner_ic'))

            # Check if exit date/time is being updated
            is_exit_update = False
            if before:
                old_exit_date = before.get('exit_date', '')
                old_exit_time = before.get('exit_time', '')
                if (not old_exit_date and not old_exit_time) and (exit_date or exit_time):
                    is_exit_update = True

            # Construct the update dictionary
            data = {
                'vehicle_plate': vehicle_plate,
                'owner_identity': owner_identity,
                'owner_phone': owner_phone,
                'entry_date': entry_date,
                'entry_time': entry_time,
                'entry_reason': entry_reason,
                'updated_at': firestore_types.SERVER_TIMESTAMP
            }
            if owner_identity in ['student', 'staff']:
                data['owner_id'] = owner_id
            if owner_name:
                data['owner_name'] = owner_name
            if owner_ic:
                data['owner_ic'] = owner_ic
            if exit_date:
                data['exit_date'] = exit_date
            if exit_time:
                data['exit_time'] = exit_time
            if 'brand' in update_data:
                data['brand'] = update_data['brand']
            if 'model' in update_data:
                data['model'] = update_data['model']

            # Add who updated the exit time
            if is_exit_update:
                if admin_id:
                    data['exit_updated_by_admin'] = admin_id
                if security_id:
                    data['exit_updated_by_security'] = security_id
                data['exit_updated_at'] = firestore_types.SERVER_TIMESTAMP

            # Update the document
            doc_ref.update(data)
            print(f"Record with ID {record_id} updated successfully.")

            # Log the action
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Updated record",
                    target_type="record",
                    target_id=record_id,
                    details={"before": before, "after": data}
                )
            elif security_id and before:
                self.add_security_action(
                    security_id=security_id,
                    action="Updated record",
                    target_type="record",
                    target_id=record_id,
                    details={"before": before, "after": data}
                )
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def delete_record(self, record_id, admin_id=None):
        try:
            doc_ref = self.db.collection('records').document(record_id)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.delete()
            
            print(f"Record with ID {record_id} deleted successfully.")
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Deleted record",
                    target_type="record",
                    target_id=record_id,
                    details=before
                )
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def search_records(self, field, value):
        try:
            records_ref = self.db.collection('records')
            query = records_ref.where(field, '==', value)
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error searching records: {e}")
            return []

    # Blacklist
    def add_blacklist_vehicle(self, plate, reason, admin_id=None):
        try:
            data = {
                'vehicle_plate': plate,
                'reason': reason,
                'created_at': firestore_types.SERVER_TIMESTAMP
            }
            
            # Add to blacklist collection using plate as document ID
            doc_ref = self.db.collection('blacklist').document(plate)
            doc_ref.set(data)
            
            print(f"Vehicle {plate} added to blacklist")
            if admin_id:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Added blacklist vehicle",
                    target_type="blacklist",
                    target_id=plate,
                    details=data
                )
            return plate
        except Exception as e:
            print(f"Error adding vehicle to blacklist: {e}")
            return None

    def update_blacklist_vehicle(self, plate, reason, admin_id=None):
        try:
            data = {
                'reason': reason,
                'updated_at': firestore_types.SERVER_TIMESTAMP
            }
            
            # Update the document
            doc_ref = self.db.collection('blacklist').document(plate)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.update(data)
            
            print(f"Vehicle {plate} updated in blacklist")
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Updated blacklist vehicle",
                    target_type="blacklist",
                    target_id=plate,
                    details={"before": before, "after": data}
                )
            return True
        except Exception as e:
            print(f"Error updating vehicle in blacklist: {e}")
            return False

    def delete_blacklist_vehicle(self, plate, admin_id=None):
        try:
            doc_ref = self.db.collection('blacklist').document(plate)
            before = doc_ref.get().to_dict() if doc_ref.get().exists else None
            doc_ref.delete()
            
            print(f"Vehicle {plate} removed from blacklist successfully.")
            if admin_id and before:
                self.add_admin_action(
                    admin_id=admin_id,
                    action="Deleted blacklist vehicle",
                    target_type="blacklist",
                    target_id=plate,
                    details=before
                )
            return True
        except Exception as e:
            print(f"Error removing vehicle from blacklist: {e}")
            return False

    def get_blacklist(self, limit=100):
        try:
            # Query the collection
            blacklist_ref = self.db.collection('blacklist')
            query = blacklist_ref.order_by('created_at', direction=firestore_types.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            # Process results
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append(data)
            
            return results
        except Exception as e:
            print(f"Error retrieving blacklist: {e}")
            return []

    def search_blacklist(self, plate):
        try:
            doc_ref = self.db.collection('blacklist').document(plate)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            print(f"Error searching blacklist: {e}")
            return None

    def get_records_by_period(self, user_type, start_date, end_date):
        try:
            records_ref = self.db.collection('records')

            query = (
                records_ref
                .where('owner_identity', '==', user_type.lower())
                .where('entry_date', '>=', start_date.strftime('%Y-%m-%d'))
                .where('entry_date', '<=', end_date.strftime('%Y-%m-%d'))
            )
            docs = query.stream()
            results = [doc.to_dict() for doc in docs]
            return results
        except Exception as e:
            print(f"Error retrieving records by period: {e}")
            return []

    # Admin log
    def _get_readable_field_name(self, field_name):

        field_mappings = {
            'record_id': 'Record ID',
            'vehicle_plate': 'Vehicle Plate',
            'owner_identity': 'Owner Identity',
            'owner_id': 'Owner ID',
            'owner_name': 'Owner Name',
            'owner_ic': 'Owner IC',
            'owner_phone': 'Owner Phone',
            'owner_email': 'Owner Email',
            'owner_address': 'Owner Address',
            'entry_date': 'Entry Date',
            'entry_time': 'Entry Time',
            'exit_date': 'Exit Date',
            'exit_time': 'Exit Time',
            'entry_reason': 'Entry Reason',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'security_id': 'Security ID',
            'security_name': 'Security Name',
            'security_ic': 'Security IC',
            'security_phone': 'Security Phone',
            'security_email': 'Security Email',
            'security_address': 'Security Address',
            'admin_id': 'Admin ID',
            'admin_name': 'Admin Name',
            'admin_ic': 'Admin IC',
            'admin_phone': 'Admin Phone',
            'admin_email': 'Admin Email',
            'admin_address': 'Admin Address'
        }
        return field_mappings.get(field_name, field_name.replace('_', ' ').title())

    def add_admin_action(self, admin_id, action, target_type, target_id, details=None):
        try:
            if target_type == 'security':
                if action.startswith('Added'):
                    action = 'Added security'
                elif action.startswith('Updated'):
                    action = 'Updated security'
                elif action.startswith('Deleted'):
                    action = 'Deleted security'

            if details and isinstance(details, dict):
                readable_details = {}
                for key, value in details.items():
                    if isinstance(value, dict):
                        readable_dict = {}
                        for k, v in value.items():
                            readable_key = self._get_readable_field_name(k)
                            readable_dict[readable_key] = v
                        readable_details[key] = readable_dict
                    else:
                        readable_key = self._get_readable_field_name(key)
                        readable_details[readable_key] = value
                details = readable_details

            log_entry = {
                'admin_id': admin_id,
                'action': action,
                'timestamp': firestore_types.SERVER_TIMESTAMP,
                'target_type': target_type.replace('_', ' ').title(),
                'target_id': target_id,
                'details': details or {}
            }
            doc_ref = self.db.collection('admin_actions').document()
            doc_ref.set(log_entry)
            print(f"Admin action logged: {action} by {admin_id} on {target_type} {target_id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error logging admin action: {e}")
            return None

    def get_admin_actions(self, limit=None):
        try:
            # Create a query reference to the admin_actions collection
            query = self.db.collection('admin_actions').order_by('timestamp', direction='DESCENDING')
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query and get documents
            docs = query.get()
            
            # Convert documents to list of dictionaries with timestamp
            actions = []
            for doc in docs:
                action_data = doc.to_dict()
                actions.append(action_data)
            
            return actions
        except Exception as e:
            print(f"Error fetching admin actions: {e}")
            return []

    # Security log
    def add_security_action(self, security_id, action, target_type, target_id, details=None):
        try:
            # Convert field names in details to readable format if details exist
            if details and isinstance(details, dict):
                readable_details = {}
                for key, value in details.items():
                    if isinstance(value, dict):
                        readable_dict = {}
                        for k, v in value.items():
                            readable_key = self._get_readable_field_name(k)
                            readable_dict[readable_key] = v
                        readable_details[key] = readable_dict
                    else:
                        readable_key = self._get_readable_field_name(key)
                        readable_details[readable_key] = value
                details = readable_details

            log_entry = {
                'security_id': security_id,
                'action': action,
                'timestamp': firestore_types.SERVER_TIMESTAMP,
                'target_type': target_type.replace('_', ' ').title(),
                'target_id': target_id,
                'details': details or {}
            }
            doc_ref = self.db.collection('security_actions').document()
            doc_ref.set(log_entry)
            print(f"Security action logged: {action} by {security_id} on {target_type} {target_id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error logging security action: {e}")
            return None

    def get_security_actions(self, limit=None):
        try:
            query = self.db.collection('security_actions').order_by('timestamp', direction='DESCENDING')
            if limit:
                query = query.limit(limit)
            docs = query.get()
            actions = []
            for doc in docs:
                action_data = doc.to_dict()
                actions.append(action_data)
            return actions
        except Exception as e:
            print(f"Error fetching security actions: {e}")
            return []

    def get_warning_alerts(self, limit=100):
        try:
            query = self.db.collection('warning_alerts').order_by('timestamp', direction=firestore_types.Query.DESCENDING)
            if limit:
                query = query.limit(limit)
            docs = query.get()
            alerts = []
            for doc in docs:
                data = doc.to_dict()
                alerts.append(data)
            return alerts
        except Exception as e:
            print(f"Error fetching warning alerts: {e}")
            return []

    def get_critical_alerts(self, limit=100):
        try:
            query = self.db.collection('critical_alerts').order_by('timestamp', direction=firestore_types.Query.DESCENDING)
            if limit:
                query = query.limit(limit)
            docs = query.get()
            alerts = []
            for doc in docs:
                data = doc.to_dict()
                alerts.append(data)
            return alerts
        except Exception as e:
            print(f"Error fetching critical alerts: {e}")
            return []

    def get_information_alerts(self, limit=100):
        try:
            query = self.db.collection('information_alerts').order_by('timestamp', direction=firestore_types.Query.DESCENDING)
            if limit:
                query = query.limit(limit)
            docs = query.get()
            alerts = []
            for doc in docs:
                data = doc.to_dict()
                alerts.append(data)
            return alerts
        except Exception as e:
            print(f"Error fetching information alerts: {e}")
            return []

    def mark_alerts_as_seen(self, alert_type, alert_ids, user_id):
        collection_map = {
            "critical": "critical_alerts",
            "warning": "warning_alerts",
            "information": "information_alerts"
        }
        collection = collection_map[alert_type]
        for alert_id in alert_ids:
            doc_ref = self.db.collection(collection).document(alert_id)
            doc_ref.update({
                "seen_by": firestore_types.ArrayUnion([user_id])
            })

    def get_alerts_with_ids(self, alert_type, limit=100):
        collection_map = {
            "critical": "critical_alerts",
            "warning": "warning_alerts",
            "information": "information_alerts"
        }
        collection = collection_map[alert_type]
        query = self.db.collection(collection)
        query = query.order_by('timestamp', direction=firestore_types.Query.DESCENDING)
        if limit:
            query = query.limit(limit)
        docs = query.get()
        alerts = []
        for doc in docs:
            data = doc.to_dict()
            data['doc_id'] = doc.id
            alerts.append(data)
        return alerts

    def is_plate_blacklisted(self, plate):
        try:
            # Always use uppercase for both input and Firestore document ID
            plate = plate.strip().upper()
            doc_ref = self.db.collection('blacklist').document(plate)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False

    def add_critical_alert(self, message, security_id, security_name, gate_name, plate):
        import datetime
        now = datetime.datetime.now()
        alert = {
            "message": message,
            "security_id": security_id,
            "security_name": security_name,
            "gate_name": gate_name,
            "plate": plate,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "seen_by": [],
            "timestamp": now,
        }
        try:
            self.db.collection('critical_alerts').add(alert)
            print(f"Critical alert logged: {message}")
        except Exception as e:
            print(f"Error logging critical alert: {e}")

    def add_warning_alert(self, message, security_id=None, security_name=None, gate_name=None, plate=None, user_id=None, role=None):
        import datetime
        now = datetime.datetime.now()
        alert = {
            "message": message,
            "security_id": security_id,
            "security_name": security_name,
            "gate_name": gate_name,
            "plate": plate,
            "user_id": user_id,
            "role": role,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "seen_by": [],
            "timestamp": now,
        }
        alert = {k: v for k, v in alert.items() if v is not None}
        try:
            self.db.collection('warning_alerts').add(alert)
            print(f"Warning alert logged: {message}")
        except Exception as e:
            print(f"Error logging warning alert: {e}")

