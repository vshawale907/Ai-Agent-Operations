const dummyData = {
  "employees": [
    { "id": 1, "name": "Alice Smith", "department": "Engineering", "role": "Frontend Engineer" },
    { "id": 2, "name": "Bob Jones", "department": "Sales", "role": "Account Executive" },
    { "id": 3, "name": "Charlie Davis", "department": "Engineering", "role": "Backend Engineer" },
    { "id": 4, "name": "Diana Prince", "department": "Marketing", "role": "Marketing Manager" }
  ],
  "departments": [
    { "id": "dept_eng", "name": "Engineering", "budget": 500000 },
    { "id": "dept_sales", "name": "Sales", "budget": 300000 },
    { "id": "dept_mktg", "name": "Marketing", "budget": 200000 }
  ],
  "projects": [
    { "id": "p1", "name": "AI Agent Migration", "department": "Engineering", "status": "In Progress", "deadline": "2026-11-01" },
    { "id": "p2", "name": "Q4 Marketing Campaign", "department": "Marketing", "status": "Planning", "deadline": "2026-10-15" }
  ],
  "tasks": [
    { "id": "t1", "projectId": "p1", "assigneeId": 1, "title": "Implement UI Fixes", "status": "Done", "priority": "High" },
    { "id": "t2", "projectId": "p1", "assigneeId": 3, "title": "Database Integration", "status": "In Progress", "priority": "Critical" },
    { "id": "t3", "projectId": "p2", "assigneeId": 4, "title": "Ad Creatives", "status": "Todo", "priority": "Medium" }
  ]
};

module.exports = dummyData;
