def get_tasks_keyboard(tasks):
    """Gera um teclado inline listando as tarefas com botões para alternar ou apagar."""
    keyboard = []
    for task in tasks:
        status_icon = "✅" if task.get("concluida") else "🔲"
        titulo = task.get("titulo")
        task_id = task.get("id")
        
        # Linha da tarefa: Botão de alternar status e Botão de excluir
        keyboard.append([
            {"text": f"{status_icon} {titulo}", "callback_data": f"task_toggle_{task_id}"},
            {"text": "🗑️", "callback_data": f"task_del_{task_id}"}
        ])
    
    # Botão para adicionar nova tarefa e voltar ao menu
    keyboard.append([
        {"text": "➕ Nova Tarefa", "callback_data": "task_new_prompt"},
        {"text": "🏠 Voltar", "callback_data": "main_menu"}
    ])
    return {"inline_keyboard": keyboard}