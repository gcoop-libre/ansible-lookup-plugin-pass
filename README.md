# Ansible Pass Lookup Plugin

> Ansible lookup plugin for ZXC24's [pass][0]  password manager.

This lookup plugin allows you to use a [pass][0] compatible password store to
generate passwords. It mimics de behaviour of the password lookup, but using pass
instead of plaintext files for storing the passwords.

If the password doesn't exist it will be generated.

## Usage

First, add in `ansible.cfg` the next line:

```
lookup_plugins=~/ansible-lookup-plugin-pass/lookup_plugins
```

Just use it as you would use the password lookup, but with the path to your
password instead of the path to a file. For example, if you would normally get
your password with

```
$ pass path/to/your/password
```

you would get it like this in a playbook

```yaml
vars:
    password: "{{ lookup('pass', 'path/to/your/password') }}"

tasks:

    - name: set password for user debian                                
      user: name=debian                                               
            password='{{ password | password_hash('sha512') }}'       
            state=present                                             
            shell=/bin/bash 
```

By default it uses `~/.password-store` as the password store. If you need to
change this set the `ANSIBLE_PASS_PASSWORD_STORE_DIR` environment variable to the
absolute path of the password store you want to use.


## Parameters

You can use parameters to control how `pass generate` will be called.

* **`length`:** length of the generated password (default: `32`).
* **`symbols`:** include symbols in the generated password (default: `False`).

### Example

```yaml
password: "{{ lookup('pass', 'path/to/your/password length=16 symbols=True') }}"

```


[0]: https://www.passwordstore.org/ "pass"
