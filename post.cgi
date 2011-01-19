#! /usr/bin/env ruby
$KCODE = 'UTF8'

$:.unshift('./lib')

require 'fileutils'
require 'tempfile'
require 'tmpdir'
require 'time'

$base_dir = '.'
require 'app'
require 'log'

err = {
  :require  => '必須なパラメータ "%s" が指定されませんでした',
  # 'parameter "%s" is required',
  :invalid  => '不正なパラメータ "%s" が指定されました',
  # 'invalid parameter "%s"',
  :capacity => '頻度が高すぎるためリクエストを拒否しました',
  # 'over capacity',
  :unzip    => 'アップロードされたファイルの展開に失敗しました',
  # 'unable to unzip the uploaded file',
  :build    => '自動コンパイルチェックに失敗しました; 提出要件を満たしているか確認して下さい',
  :build_fatal => '自動コンパイルチェックに失敗しました; TAに問い合わせて下さい',
}

app = App.new
time = Time.now

id = 'report_id'
rep_id = app.cgi.params[id][0].read
raise ArgumentError, (err[:require] % id) unless defined?(rep_id)

rep_schemes = app.file(:scheme)['scheme'] || []
rep_defined = rep_schemes.any?{|r| r['id'] == rep_id}
raise ArgumentError, (err[:invalid] % rep_id) unless rep_defined

USER_DIR = app.user_dir(rep_id)
log_file = USER_DIR[App::FILES[:log]]

begin
  begin
    src_dir = USER_DIR + time.iso8601 + 'src'
    raise RuntimeError, err[:capacity] if File.exist?(src_dir.to_s)

    FileUtils.mkdir_p(src_dir.to_s)
    file = app.cgi.params['report_file'][0]

    unless file.path then
      tmp = Tempfile.open('report.zip')
      tmp.write(file.read)
      file = tmp
    end
    path = file.path
    file.close

    # extract archive file
    res = system("env 7z x -o#{src_dir} #{path} > /dev/null 2>&1")
    raise RuntimeError, err[:unzip] unless res

    entries = Dir.glob("#{src_dir}/*")

    # extract tar file
    if entries.length == 1 && entries[0] =~ /\.tar$/
      Dir.chdir(src_dir.to_s) do
        file = File.basename(entries[0])
        res = system("tar xf '#{file}' > /dev/null 2>&1 && rm '#{file}'")
      end
      raise RuntimeError, err[:unzip] unless res
      entries = Dir.glob("#{src_dir}/*")
    end

    # move files from a single directory to the parent directory
    if entries.length == 1 && File.directory?(entries[0]) then
      entries_dir = entries[0]
      Dir.mktmpdir do |tmpdir|
        src_files = Dir.glob("#{entries_dir}/*", File::FNM_DOTMATCH)
        src_files.reject!{|f| f =~ /\/\.+$/}
        FileUtils.mv(src_files, tmpdir)
        FileUtils.rmdir(entries_dir)
        FileUtils.mv(Dir.glob("#{tmpdir}/*"), src_dir.to_s)
      end
    end

    # solved exercises
    report = []
    app.cgi.params.each do |k,v|
      report << k if k =~ /#{app.file(:scheme)['regex']}/
    end
    Log.new(log_file, time) do |log|
      log.write_data('status' => 'build', 'report' => report)
    end

    # run build checker
    cmd = "#{App::FILES[:build]} '#{rep_id}' '#{app.user}' '#{time.iso8601}'"
    cmd = ([cmd]+report).join(' ')
    build = nil
    if system("#{cmd} > /dev/null 2>#{USER_DIR['build_fatal.log']}")
      Log.new(log_file, time) do |log|
        hash = {
          'status' => 'build:NG',
          'log'    => {
            'error'   => log.build['detail'],
            'message' => err[:build] }
        }

        if log.build['status'] == 'OK'
          build = true
          hash = { 'status' => 'check', 'log' => { 'build'  => 'OK' } }
        end

        log.write_data(hash.merge('timestamp' => log.build['timestamp']))
      end
    else
      raise RuntimeError, err[:build_fatal]
    end

    exit unless build

    # invoke tester in a sandbox
    cmd = "#{App::FILES[:sandbox]} '#{rep_id}' '#{app.user}' '#{time.iso8601}'"
    cmd = "#{cmd} > /dev/null 2>&1 &" # do not wait
    system(cmd)

  rescue RuntimeError => e
    Log.new(log_file, time) do |log|
      log.write_data('status' => 'NG', 'log' => { 'error' => e.to_s })
    end
  end
ensure
  print app.cgi.header('status' => '302 Found', 'Location' => './record/')
end
