"""Serialize the pinned matron clock reader with JACK client destruction."""
import difflib


def apply(source):
    path = source / 'matron/src/jack_client.c'
    before = path.read_text()
    after = before
    replacements = [
        ('// protects access to g_last_total_frames.',
         '// protects the clock client lifetime and g_last_total_frames.'),
        ('    jack_client_close(jack_client);',
         '    pthread_mutex_lock(&g_time_lock);\n'
         '    if (jack_client != NULL) {\n'
         '        jack_client_close(jack_client);\n'
         '        jack_client = NULL;\n'
         '    }\n'
         '    pthread_mutex_unlock(&g_time_lock);'),
        ('    return jack_cpu_load(jack_client);',
         '    pthread_mutex_lock(&g_time_lock);\n'
         '    float result = jack_client != NULL ? jack_cpu_load(jack_client) : 0;\n'
         '    pthread_mutex_unlock(&g_time_lock);\n'
         '    return result;'),
        ('    uint32_t current_frames = (uint32_t)jack_frame_time(jack_client);\n\n'
         '    pthread_mutex_lock(&g_time_lock);',
         '    pthread_mutex_lock(&g_time_lock);\n'
         '    // Clock threads can outlive cleanup; freeze time after client close.\n'
         '    uint32_t current_frames = jack_client != NULL\n'
         '        ? (uint32_t)jack_frame_time(jack_client) : (uint32_t)g_last_total_frames;'),
        ('    return (double)result / jack_sample_rate;',
         '    return jack_sample_rate > 0 ? (double)result / jack_sample_rate : 0;'),
    ]
    for old, new in replacements:
        if after.count(old) != 1:
            raise ValueError('Pinned JACK client changed; inspect lifetime patch')
        after = after.replace(old, new)
    path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='a/matron/src/jack_client.c', tofile='b/matron/src/jack_client.c'))
